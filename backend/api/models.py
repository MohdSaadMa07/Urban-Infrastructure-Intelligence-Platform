from django.contrib.gis.db import models


class Ward(models.Model):
    name = models.CharField(max_length=100)

    boundary = models.MultiPolygonField()

    def __str__(self):
        return self.name