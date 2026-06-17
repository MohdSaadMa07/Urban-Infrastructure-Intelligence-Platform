from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from api.models import Ward
import json

def home(request):
    return JsonResponse({
        "message": "API is working "
    })

@api_view(['GET'])
def identify_ward(request):
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    
    if not lat or not lng:
        return Response({'error': 'Please provide lat and lng'}, status=400)
        
    try:
        # PostGIS uses (longitude, latitude) for Point
        point = Point(float(lng), float(lat), srid=4326)
        
        # Native spatial query
        ward = Ward.objects.filter(boundary__contains=point).first()
        
        if ward:
            return Response({
                'ward_name': ward.ward_name,
                'ward_no': ward.ward_no
            })
        else:
            return Response({'message': 'No ward found for this location'}, status=404)
            
    except ValueError:
        return Response({'error': 'Invalid coordinates'}, status=400)

@api_view(['GET'])
def wards_geojson(request):
    # Retrieve all wards
    wards = Ward.objects.all()
    
    features = []
    for ward in wards:
        feature = {
            "type": "Feature",
            "properties": {
                "ward_no": ward.ward_no,
                "ward_name": ward.ward_name
            },
            "geometry": json.loads(ward.boundary.geojson)
        }
        features.append(feature)
        
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return Response(geojson)