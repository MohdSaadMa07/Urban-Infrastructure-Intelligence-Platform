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