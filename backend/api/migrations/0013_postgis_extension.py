from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_complaint_sender_phone_complaint_source'),
    ]

    operations = [
        CreateExtension('postgis'),
    ]
