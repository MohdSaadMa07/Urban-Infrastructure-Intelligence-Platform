"""
WhatsApp bot powered by Twilio.
Handles incoming messages, maintains a simple conversation state,
and creates / responds to complaints via WhatsApp.
"""

import io
import json
import logging
import re
from datetime import datetime

from django.conf import settings
from django.contrib.gis.geos import Point
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from api.models import Complaint, Ward

logger = logging.getLogger(__name__)

# ── In-memory conversation state per sender (phone) ──────────────────────
# WARNING: In-memory only. State is lost on server restart.
# NOTE: A Redis-backed session store migration is required for production.
CONV_STORE: dict[str, dict] = {}

CONV_STEPS = frozenset({'category', 'description', 'photo', 'location', 'confirm', 'done'})


def _extract_address(wid: str) -> str:
    """Return a short address from the WhatsApp location message."""
    return wid.split('/')[-1] if '/' in wid else wid


def _validate_location(lat: float, lng: float) -> Ward | None:
    """Return the Ward that contains (lat, lng), or None."""
    point = Point(lng, lat, srid=4326)
    return Ward.objects.filter(boundary__contains=point).first()


def _reply(to: str, body: str) -> HttpResponse:
    """Return a TwiML <Message> response."""
    from twilio.twiml.messaging_response import MessagingResponse
    r = MessagingResponse()
    r.message(body)
    return HttpResponse(str(r), content_type='application/xml')


def _media_reply(to: str, body: str, media_url: str) -> HttpResponse:
    """Return a TwiML <Message> with image."""
    from twilio.twiml.messaging_response import MessagingResponse, Message
    r = MessagingResponse()
    msg = Message()
    msg.body(body)
    msg.media(media_url)
    r.append(msg)
    return HttpResponse(str(r), content_type='application/xml')


def send_status_update(complaint_id: int, new_status: str, phone: str) -> None:
    """Send a WhatsApp status update to the citizen (fire-and-forget, no TwiML)."""
    if not settings.TWILIO_ACCOUNT_SID or not phone:
        logger.warning("Twilio not configured or no phone - skipping status update for #%s", complaint_id)
        return
    label = dict(Complaint.STATUS_CHOICES).get(new_status, new_status)
    from twilio.rest import Client
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    try:
        client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=phone,
            body=(
                f"🔔 *Complaint #{complaint_id} Update*\n"
                f"Your complaint status has changed to: *{label}*\n\n"
                f"Track it anytime: https://mumbaiui.org/track?id={complaint_id}"
            ),
        )
    except Exception as exc:
        logger.warning("Twilio status update failed for #%s: %s", complaint_id, exc)


def _download_and_save_image(url: str, complaint: Complaint) -> None:
    """Download an image from url and save it to complaint.image."""
    import requests
    from django.core.files.base import ContentFile
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        ext = 'jpg'
        complaint.image.save(f'wa_{complaint.id}.{ext}', ContentFile(resp.content), save=True)
    except Exception as exc:
        logger.warning("Could not download WhatsApp image for #%s: %s", complaint.id, exc)


def _resolve_ward(text: str) -> Ward | None:
    """Try multiple strategies to match a ward from user text input."""
    clean = text.strip().lower()

    # 1. Exact match (case-insensitive)
    ward = Ward.objects.filter(ward_name__iexact=clean).first()
    if ward:
        return ward

    # 2. Strip "ward " prefix
    if clean.startswith('ward '):
        ward = Ward.objects.filter(ward_name__iexact=clean[5:].strip()).first()
        if ward:
            return ward

    # 3. Remove slashes/hyphens and compare: "k/e" -> "ke"
    no_sep = clean.replace('/', '').replace('-', '').replace(' ', '')
    for w in Ward.objects.all():
        w_clean = w.ward_name.lower().replace('/', '').replace('-', '').replace(' ', '')
        if w_clean == no_sep:
            return w

    # 4. Single letter match: "a" -> "A"
    if len(clean) == 1 and clean.isalpha():
        ward = Ward.objects.filter(ward_name__iexact=clean.upper()).first()
        if ward:
            return ward

    return None


def _build_confirm_summary(state: dict) -> str:
    return (
        f"📋 *Summary*\n"
        f"Category: {state.get('category', '?')}\n"
        f"Description: {state.get('description', '?')[:80]}\n"
        f"Location: {state.get('ward_name', '?')}\n\n"
        f"Reply *CONFIRM* to submit or *CANCEL* to start over."
    )


@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    """
    Twilio inbound webhook.
    Expects POST with: From, Body, NumMedia, MediaUrl0 (optional),
    Latitude/Longitude (optional).
    """
    from_ = request.POST.get('From', '').strip()          # e.g. "whatsapp:+919876543210"
    body = request.POST.get('Body', '').strip()
    num_media = int(request.POST.get('NumMedia', 0))
    media_url0 = request.POST.get('MediaUrl0', '').strip()
    lat_str = request.POST.get('Latitude', '').strip()
    lng_str = request.POST.get('Longitude', '').strip()

    if not from_:
        return HttpResponse("Missing From", status=400)

    phone = from_.replace('whatsapp:', '')

    # Initialise conversation state
    if phone not in CONV_STORE:
        CONV_STORE[phone] = {'step': 'greeting'}
    state = CONV_STORE[phone]
    step = state.get('step', 'greeting')

    # ── Reset command ───────────────────────────────────────────────
    if body.upper() in ('RESET', 'CANCEL', 'START'):
        CONV_STORE[phone] = {'step': 'greeting'}
        return _reply(from_, (
            "🔄 *Let's start over.*\n\n"
            "I am *MumbaiUI Bot* 🤖 — I help you file civic complaints on WhatsApp.\n\n"
            "Reply with the *category* of your issue:\n"
            "• 🛣 Pothole\n"
            "• 💧 Water Supply\n"
            "• 💡 Street Light\n"
            "• 🗑 Garbage\n"
            "• 🌊 Drainage\n"
            "• 🚧 Road\n"
            "• 🔧 Other"
        ))

    # ── Handle media (photo) when in photo step ─────────────────────
    if step == 'photo' and num_media > 0 and media_url0:
        state['media_url'] = media_url0
        state['step'] = 'location'
        return _reply(from_, (
            "✅ Photo received.\n\n"
            "Now send me your *location* (tap the 📎 → Location).\n"
            "Or type your ward code (e.g. *K/E*, *F/S*, *H/W*)."
        ))

    # ── Handle location coordinates ─────────────────────────────────
    if step == 'location' and lat_str and lng_str:
        try:
            lat = float(lat_str)
            lng = float(lng_str)
            ward = _validate_location(lat, lng)
            if not ward:
                return _reply(from_, (
                    "❌ That location doesn't fall within any known ward.\n"
                    "Please try again with a more precise location."
                ))
            state['latitude'] = lat
            state['longitude'] = lng
            state['ward_name'] = ward.ward_name
            state['ward'] = ward
        except (ValueError, TypeError):
            return _reply(from_, "❌ Invalid coordinates. Please send location again.")
    elif step == 'location' and body:
        ward = _resolve_ward(body)
        if ward:
            state['ward_name'] = ward.ward_name
            state['ward'] = ward
        else:
            return _reply(from_, (
                f"❌ Ward '{body}' not found. Try again or send your location via 📎 → Location."
            ))

    # ── Step router ──────────────────────────────────────────────────
    if step == 'greeting':
        categories = "\n".join(
            f"• {c[1]}" for c in Complaint.CATEGORY_CHOICES
        )
        CONV_STORE[phone] = {'step': 'category'}
        return _reply(from_, (
            "👋 Welcome to *MumbaiUI WhatsApp Bot*!\n\n"
            "I'll help you file a complaint in 4 easy steps.\n\n"
            f"*Step 1:* What's the issue category?\n{categories}\n\n"
            "Just type the category name."
        ))

    elif step == 'category':
        category = body.strip().lower()
        valid = {c[0].lower(): c[0] for c in Complaint.CATEGORY_CHOICES}
        matched = valid.get(category)
        if not matched:
            return _reply(from_, (
                "❌ Sorry, I didn't recognise that category.\n"
                "Please type one of: Pothole, Water Supply, Street Light, "
                "Garbage, Drainage, Road, Other."
            ))
        state['category'] = matched
        state['step'] = 'description'
        return _reply(from_, (
            f"✅ *{dict(Complaint.CATEGORY_CHOICES).get(matched, matched)}* selected.\n\n"
            f"*Step 2:* Briefly describe the problem.\n"
            f"(e.g. *Large pothole near the bus stop causing accidents*)"
        ))

    elif step == 'description':
        if len(body) < 5:
            return _reply(from_, "Please provide a bit more detail (at least 5 characters).")
        state['description'] = body
        state['step'] = 'photo'
        return _reply(from_, (
            "✅ Description saved.\n\n"
            "*Step 3:* Send a *photo* of the issue 📸\n"
            "Tap 📎 → Image. (Or type *SKIP* to continue without a photo.)"
        ))

    elif step == 'photo':
        if body.upper() == 'SKIP':
            state['step'] = 'location'
            return _reply(from_, (
                "⏩ Photo skipped.\n\n"
                "*Step 4 (final):* Send your *location* 📍\n"
                "Tap 📎 → Location. Or type your ward code (e.g. *K/E*, *A*, *F/S*)."
            ))
        return _reply(from_, (
            "📸 Please send a photo using 📎 → Image,\n"
            "or type *SKIP* to continue without one."
        ))

    elif step == 'location':
        return _reply(from_, (
            "📍 Please share your location (📎 → Location)\n"
            "or type your ward (e.g. *K/E*, *A*, *F/S*, *ward b*)."
        ))

    elif step == 'confirm':
        if body.upper() == 'CONFIRM':
            try:
                c = Complaint.objects.create(
                    ward=state.get('ward'),
                    category=state.get('category', 'Other'),
                    description=state.get('description', ''),
                    latitude=state.get('latitude'),
                    longitude=state.get('longitude'),
                    sender_phone=phone,
                    source='whatsapp',
                )
                if state.get('media_url'):
                    _download_and_save_image(state['media_url'], c)

                del CONV_STORE[phone]
                return _reply(from_, (
                    f"✅ *Complaint #{c.id} filed successfully!*\n\n"
                    f"Your complaint has been registered in *{c.ward.ward_name}*.\n"
                    f"Your local councillor will be notified.\n\n"
                    f"📌 *Track it:* https://mumbaiui.org/track?id={c.id}\n"
                    f"Reply *STATUS {c.id}* to check updates anytime.\n\n"
                    f"Reply *START* to file another complaint."
                ))
            except Exception as exc:
                logger.exception("WhatsApp complaint creation failed")
                return _reply(from_, (
                    "❌ Something went wrong while saving your complaint.\n"
                    "Please try again by replying *START*."
                ))
        elif body.upper() == 'CANCEL':
            del CONV_STORE[phone]
            return _reply(from_, "❌ Cancelled. Reply *START* to begin again.")
        else:
            return _reply(from_, (
                "Please reply *CONFIRM* to submit or *CANCEL* to start over.\n\n"
                + _build_confirm_summary(state)
            ))

    # ── After location is collected, move to confirm ────────────────
    if state.get('ward'):
        state['step'] = 'confirm'
        return _reply(from_, _build_confirm_summary(state))

    # ── Fallback ────────────────────────────────────────────────────
    return _reply(from_, (
        "I didn't understand that. Reply *START* to begin filing a complaint, "
        "or *RESET* to start over."
    ))
