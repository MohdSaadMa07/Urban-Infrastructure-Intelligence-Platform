from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    home, identify_ward, wards_geojson, health_scores,
    submit_complaint, list_complaints, councillors,
    get_complaint, update_complaint_status, trend_data,
    councillor_ward_dashboard, complaint_hotspots,
)
from .auth_views import register, login_view, profile, logout_view
from .models import Ward
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import WardSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def wards_list(request):
    wards = Ward.objects.all().order_by('ward_name')
    return Response(WardSerializer(wards, many=True).data)

urlpatterns = [
    path('', home),
    path('identify-ward/', identify_ward, name='identify-ward'),
    path('wards-geojson/', wards_geojson, name='wards-geojson'),
    path('health-scores/', health_scores, name='health-scores'),
    path('complaints/', list_complaints, name='list-complaints'),
    path('complaints/submit/', submit_complaint, name='submit-complaint'),
    path('complaints/<int:pk>/', get_complaint, name='get-complaint'),
    path('complaints/<int:pk>/status/', update_complaint_status, name='update-complaint-status'),
    path('councillors/', councillors, name='councillors'),
    path('trends/', trend_data, name='trend-data'),
    path('hotspots/', complaint_hotspots, name='complaint-hotspots'),
    path('wards/', wards_list, name='wards-list'),
    path('councillor/dashboard/', councillor_ward_dashboard, name='councillor-dashboard'),
    path('auth/register/', register, name='auth-register'),
    path('auth/login/', login_view, name='auth-login'),
    path('auth/login/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/profile/', profile, name='auth-profile'),
    path('auth/logout/', logout_view, name='auth-logout'),
]