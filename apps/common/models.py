import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model providing self-updating `created_at` and `updated_at` fields.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class UUIDTimeStampedModel(TimeStampedModel):
    """
    Abstract model combining UUID primary key with timestamp tracking.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class ContactMessage(UUIDTimeStampedModel):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField(max_length=5000)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return self.subject


class SiteContent(models.Model):
    key = models.SlugField(primary_key=True)
    title = models.CharField(max_length=200)
    body = models.TextField(max_length=5000)

    def __str__(self):
        return self.title
