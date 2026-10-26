import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.common.models import UUIDTimeStampedModel


class EmploymentTypePreference(models.TextChoices):
    FULL_TIME = "FULL_TIME", _("Full Time")
    PART_TIME = "PART_TIME", _("Part Time")
    CONTRACT = "CONTRACT", _("Contract")
    FREELANCE = "FREELANCE", _("Freelance")
    INTERNSHIP = "INTERNSHIP", _("Internship")
    ANY = "ANY", _("Any")


class RemoteWorkPreference(models.TextChoices):
    ONSITE = "ONSITE", _("On-site Only")
    REMOTE = "REMOTE", _("Remote Only")
    HYBRID = "HYBRID", _("Hybrid")
    ANY = "ANY", _("Open to Any")


class CandidateProfile(UUIDTimeStampedModel):
    """
    Candidate professional profile linked one-to-one to a User account.
    Includes privacy controls and profile completeness tracking.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_profile",
    )
    professional_title = models.CharField(_("professional title"), max_length=200, blank=True, db_index=True)
    biography = models.TextField(_("biography"), blank=True)
    location = models.CharField(_("location"), max_length=255, blank=True)
    country = models.CharField(_("country"), max_length=100, blank=True, db_index=True)
    phone = models.CharField(_("phone number"), max_length=50, blank=True)
    years_of_experience = models.PositiveIntegerField(_("years of experience"), default=0)

    employment_type_preference = models.CharField(
        _("employment type preference"),
        max_length=20,
        choices=EmploymentTypePreference.choices,
        default=EmploymentTypePreference.FULL_TIME,
    )
    remote_work_preference = models.CharField(
        _("remote work preference"),
        max_length=20,
        choices=RemoteWorkPreference.choices,
        default=RemoteWorkPreference.ANY,
    )

    # Privacy Controls
    is_public = models.BooleanField(
        _("is profile publicly searchable"),
        default=True,
        help_text=_("Allow verified employers to discover this profile in search."),
    )
    is_contact_visible = models.BooleanField(
        _("is contact details visible to verified employers"),
        default=False,
        help_text=_("Allow verified employers to directly see phone number before application submission."),
    )

    class Meta:
        verbose_name = _("candidate profile")
        verbose_name_plural = _("candidate profiles")
        indexes = [
            models.Index(fields=["professional_title", "country"]),
            models.Index(fields=["years_of_experience"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.professional_title or 'Candidate'})"

    @property
    def completeness_score(self) -> int:
        """
        Calculates profile completeness percentage (0 to 100).
        """
        weights = [
            (bool(self.professional_title), 20),
            (bool(self.biography and len(self.biography.strip()) > 30), 20),
            (bool(self.location and self.country), 15),
            (bool(self.phone), 10),
            (bool(self.years_of_experience > 0), 15),
            (bool(self.employment_type_preference), 10),
            (bool(self.remote_work_preference), 10),
        ]
        return sum(score for fulfilled, score in weights if fulfilled)


class CandidateSkill(UUIDTimeStampedModel):
    """
    Skill possessed by a candidate with self-reported years of experience.
    """
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="skills",
    )
    skill = models.ForeignKey(
        "jobs.Skill",
        on_delete=models.CASCADE,
        related_name="candidate_skills",
    )
    years_of_experience = models.PositiveIntegerField(_("years of experience"), default=1)

    class Meta:
        verbose_name = _("candidate skill")
        verbose_name_plural = _("candidate skills")
        unique_together = ("candidate", "skill")
        indexes = [
            models.Index(fields=["candidate", "skill"]),
        ]

    def __str__(self):
        return f"{self.candidate.user.get_full_name()} - {self.skill.name} ({self.years_of_experience} yrs)"
