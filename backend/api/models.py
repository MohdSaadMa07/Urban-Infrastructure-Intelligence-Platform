from django.contrib.gis.db import models

class Ward(models.Model):
    ward_no = models.IntegerField()
    ward_name = models.CharField(max_length=100)

    boundary = models.MultiPolygonField()

    def __str__(self):
        return self.ward_name