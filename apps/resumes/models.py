import os
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.common.models import UUIDTimeStampedModel
from apps.resumes.storage import PrivateResumeStorage
from apps.common.validators import validate_resume_file
from apps.candidates.models import CandidateProfile


def resume_upload_path(instance, filename):
    """
    Generate an isolated, non-guessable storage path for candidate resumes.
    Example: resumes/<candidate_id>/<uuid>.<ext>
    """
    ext = os.path.splitext(filename)[1].lower()
    return f"resumes/{instance.candidate.id}/{uuid.uuid4()}{ext}"


class Resume(UUIDTimeStampedModel):
    """
    Encrypted/protected resume document belonging to a CandidateProfile.
    """
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="resumes",
    )
    title = models.CharField(_("resume title"), max_length=255)
    file = models.FileField(
        _("resume file"),
        upload_to=resume_upload_path,
        storage=PrivateResumeStorage(),
        validators=[validate_resume_file],
    )
    original_filename = models.CharField(_("original filename"), max_length=255)
    file_type = models.CharField(_("file MIME type"), max_length=100)
    file_size = models.PositiveIntegerField(_("file size in bytes"))
    is_default = models.BooleanField(_("is default resume"), default=False, db_index=True)

    class Meta:
        verbose_name = _("resume")
        verbose_name_plural = _("resumes")
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(fields=["candidate", "is_default"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.candidate.user.get_full_name()}"

    def set_as_default(self):
        """Sets this resume as default and unsets any previous default."""
        Resume.objects.filter(candidate=self.candidate, is_default=True).exclude(pk=self.pk).update(is_default=False)
        self.is_default = True
        self.save(update_fields=["is_default", "updated_at"])

    @property
    def uploaded_at(self):
        return self.created_at
