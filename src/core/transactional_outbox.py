from django.db import models

class Outbox(models.Model):
    event_type = models.CharField(max_length=255)
    event_date_time = models.DateTimeField(auto_now_add=True)
    environment = models.CharField(max_length=255)
    event_context = models.JSONField()
    metadata_version = models.BigIntegerField()
    processed = models.BooleanField(default=False)

    class Meta:
        db_table = 'outbox'
        indexes = [
            models.Index(fields=['processed']),
        ]
