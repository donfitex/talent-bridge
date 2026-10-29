from django.conf import settings
from django.db import models
from apps.common.models import UUIDTimeStampedModel


class Notification(UUIDTimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    subject = models.CharField(max_length=255)
    message = models.TextField()
    deduplication_key = models.CharField(max_length=255, unique=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["sent_at", "created_at"])]
