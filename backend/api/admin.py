from django.contrib import admin
from .models import Ward, CivicMetrics

@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ('ward_no', 'ward_name')
    search_fields = ('ward_name',)

@admin.register(CivicMetrics)
class CivicMetricsAdmin(admin.ModelAdmin):
    list_display = ('ward', 'year', 'total_complaints', 'closed_complaints', 'escalated_complaints', 'avg_resolution_days')
    list_filter = ('year',)
    search_fields = ('ward__ward_name',)
