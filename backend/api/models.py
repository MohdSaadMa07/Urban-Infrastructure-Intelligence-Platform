from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('citizen', 'Citizen'),
        ('councillor', 'Ward Councillor'),
        ('admin', 'Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    ward = models.ForeignKey('Ward', on_delete=models.SET_NULL, null=True, blank=True, related_name='councillors')
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

class Ward(models.Model):
    ward_no = models.IntegerField()
    ward_name = models.CharField(max_length=100)
    boundary = models.MultiPolygonField()
    health_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.ward_name

class CivicMetrics(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='metrics')
    year = models.PositiveSmallIntegerField()
    total_complaints = models.IntegerField(default=0)
    closed_complaints = models.IntegerField(default=0)
    escalated_complaints = models.IntegerField(default=0)
    avg_resolution_days = models.FloatField(default=0)
    per_capita_complaints = models.IntegerField(default=0)
    total_deliberations = models.IntegerField(default=0)
    per_capita_deliberations = models.IntegerField(default=0)
    avg_councillors = models.IntegerField(default=0)

    class Meta:
        unique_together = (('ward', 'year'),)
        ordering = ['-year']

    def __str__(self):
        return f"{self.ward.ward_name} - {self.year}"


class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('pothole', 'Potholes'),
        ('water', 'Water Supply'),
        ('drainage', 'Drainage'),
        ('garbage', 'Garbage'),
        ('streetlight', 'Street Lights'),
        ('road', 'Roads'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='complaints')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    image = models.ImageField(upload_to='complaint_images/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_category_display()} - Ward {self.ward.ward_name}"


class PortalMetrics(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='portal_metrics')
    year = models.PositiveSmallIntegerField()
    total_complaints = models.IntegerField(default=0)
    resolved_complaints = models.IntegerField(default=0)

    class Meta:
        unique_together = (('ward', 'year'),)
        verbose_name_plural = 'Portal Metrics'

    def __str__(self):
        return f"{self.ward.ward_name} - {self.year} (Portal)"


class WardPrediction(models.Model):
    RISK_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    ]
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='predictions')
    prediction_date = models.DateField()
    predicted_risk = models.CharField(max_length=20, choices=RISK_CHOICES)
    predicted_complaints = models.IntegerField()
    predicted_complaints_lower = models.IntegerField(null=True, blank=True)
    predicted_complaints_upper = models.IntegerField(null=True, blank=True)
    predicted_health_score = models.FloatField(null=True, blank=True)
    recommendation = models.TextField(blank=True)
    top_features = models.JSONField(null=True, blank=True)
    model_version = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ward Prediction'
        verbose_name_plural = 'Ward Predictions'
        ordering = ['-prediction_date']

    def __str__(self):
        return f"{self.ward.ward_name} - {self.prediction_date} ({self.predicted_risk})"