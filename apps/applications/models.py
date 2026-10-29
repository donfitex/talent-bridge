import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.common.models import UUIDTimeStampedModel
from apps.jobs.models import Job
from apps.candidates.models import CandidateProfile
from apps.resumes.models import Resume


class ApplicationStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", _("Submitted")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    SHORTLISTED = "SHORTLISTED", _("Shortlisted")
    INTERVIEW = "INTERVIEW", _("Interview")
    OFFERED = "OFFERED", _("Offered")
    HIRED = "HIRED", _("Hired")
    REJECTED = "REJECTED", _("Rejected")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")


class JobApplication(UUIDTimeStampedModel):
    """
    Connects a CandidateProfile and a Job listing with resume snapshot,
    cover letter, lifecycle status, and withdrawal timestamps.
    """
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    resume = models.ForeignKey(
        Resume,
        on_delete=models.PROTECT,
        related_name="applications",
    )
    cover_letter = models.TextField(_("cover letter"), blank=True)
    status = models.CharField(
        _("application status"),
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.SUBMITTED,
        db_index=True,
    )
    internal_notes = models.TextField(_("internal recruitment notes"), blank=True)
    withdrawn_at = models.DateTimeField(_("withdrawn timestamp"), null=True, blank=True)

    class Meta:
        verbose_name = _("job application")
        verbose_name_plural = _("job applications")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "candidate"],
                condition=~models.Q(status=ApplicationStatus.WITHDRAWN),
                name="unique_active_application_per_candidate_job",
            )
        ]
        indexes = [
            models.Index(fields=["job", "status"]),
            models.Index(fields=["candidate", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.candidate.user.get_full_name()} -> {self.job.title} ({self.status})"

    @property
    def applied_at(self):
        return self.created_at

    @property
    def is_active(self) -> bool:
        return self.status not in [ApplicationStatus.WITHDRAWN, ApplicationStatus.REJECTED]


class ApplicationStatusHistory(UUIDTimeStampedModel):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name="history")
    actor = models.ForeignKey("users.User", null=True, on_delete=models.SET_NULL)
    previous_status = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at", "id"]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("Application history is append-only.")
        super().save(*args, **kwargs)
