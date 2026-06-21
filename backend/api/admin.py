from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Ward, CivicMetrics, PortalMetrics, Complaint, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'get_role', 'is_staff')
    def get_role(self, obj):
        return obj.profile.role if hasattr(obj, 'profile') else '-'
    get_role.short_description = 'Role'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

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

@admin.register(PortalMetrics)
class PortalMetricsAdmin(admin.ModelAdmin):
    list_display = ('ward', 'year', 'total_complaints', 'resolved_complaints')
    list_filter = ('year', 'ward')

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'ward', 'status', 'created_at')
    list_filter = ('status', 'category', 'ward')
    search_fields = ('description', 'ward__ward_name')
