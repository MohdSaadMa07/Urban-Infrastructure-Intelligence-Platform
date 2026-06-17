from django.contrib.gis.db import models

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
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_category_display()} - Ward {self.ward.ward_name}"