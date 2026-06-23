from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

# Serve React frontend assets
frontend_dist = settings.BASE_DIR.parent / 'frontend' / 'dist'
if frontend_dist.exists():
    urlpatterns += [
        re_path(r'^assets/(?P<path>.*)$', serve, {
            'document_root': str(frontend_dist / 'assets'),
        }),
    ]

# Serve React frontend for all other routes (SPA catch-all)
urlpatterns += [re_path(r'^.*$', TemplateView.as_view(template_name='index.html'))]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)