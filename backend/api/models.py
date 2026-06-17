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
    total_complaints = models.IntegerField()
    closed_complaints = models.IntegerField()
    escalated_complaints = models.IntegerField()
    avg_resolution_days = models.FloatField()

    class Meta:
        unique_together = (('ward', 'year'),)
        ordering = ['-year']

    def __str__(self):
        return f"{self.ward.ward_name} - {self.year}"