from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class Interview(UUIDTimeStampedModel):
    application = models.ForeignKey(
        "applications.JobApplication", on_delete=models.CASCADE, related_name="interviews"
    )
    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="interviews"
    )
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField()
    location = models.CharField(max_length=500)
    status = models.CharField(
        max_length=20,
        choices=[
            ("SCHEDULED", "Scheduled"),
            ("COMPLETED", "Completed"),
            ("CANCELLED", "Cancelled"),
        ],
        default="SCHEDULED",
    )
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ["starts_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F("starts_at")),
                name="interview_positive_duration",
            )
        ]

    def clean(self):
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "End must follow start."})
