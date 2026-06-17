from django.urls import path
from .views import home, identify_ward, wards_geojson

urlpatterns = [
    path('', home),
    path('identify-ward/', identify_ward, name='identify-ward'),
    path('wards-geojson/', wards_geojson, name='wards-geojson'),
]