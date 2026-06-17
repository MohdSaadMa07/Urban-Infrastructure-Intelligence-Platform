from django.contrib import admin
from .models import Ward, CivicMetrics, Complaint

@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ('ward_no', 'ward_name', 'health_score')
    search_fields = ('ward_name',)

@admin.register(CivicMetrics)
class CivicMetricsAdmin(admin.ModelAdmin):
    list_display = ('ward', 'year', 'total_complaints', 'closed_complaints',
                    'escalated_complaints', 'avg_resolution_days',
                    'per_capita_complaints', 'total_deliberations')
    list_filter = ('year', 'ward')
    search_fields = ('ward__ward_name',)

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'ward', 'status', 'created_at')
    list_filter = ('status', 'category', 'ward')
    search_fields = ('description', 'ward__ward_name')
