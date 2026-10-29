from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.common.models import UUIDTimeStampedModel
from apps.companies.models import Company


class JobCategory(UUIDTimeStampedModel):
    """
    Standardized taxonomy category for job listings (e.g., Software Engineering, Design).
    """

    name = models.CharField(_("category name"), max_length=100, unique=True, db_index=True)
    slug = models.SlugField(_("slug"), max_length=120, unique=True, db_index=True)
    description = models.TextField(_("description"), blank=True)
    icon = models.CharField(_("icon class"), max_length=50, blank=True, default="bi-briefcase")
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _("job category")
        verbose_name_plural = _("job categories")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Skill(UUIDTimeStampedModel):
    """
    Searchable skills taxonomy tag for jobs and candidates.
    Duplicate prevention via lowercased name validation and unique slug.
    """

    name = models.CharField(_("skill name"), max_length=100, unique=True, db_index=True)
    slug = models.SlugField(_("slug"), max_length=120, unique=True, db_index=True)
    category = models.ForeignKey(
        JobCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="skills",
    )
    is_verified = models.BooleanField(_("is verified"), default=True)

    class Meta:
        verbose_name = _("skill")
        verbose_name_plural = _("skills")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class EmploymentType(models.TextChoices):
    FULL_TIME = "FULL_TIME", _("Full Time")
    PART_TIME = "PART_TIME", _("Part Time")
    CONTRACT = "CONTRACT", _("Contract")
    TEMPORARY = "TEMPORARY", _("Temporary")
    INTERNSHIP = "INTERNSHIP", _("Internship")
    FREELANCE = "FREELANCE", _("Freelance")


class WorkplaceType(models.TextChoices):
    ONSITE = "ONSITE", _("On-site")
    REMOTE = "REMOTE", _("Remote")
    HYBRID = "HYBRID", _("Hybrid")


class ExperienceLevel(models.TextChoices):
    ENTRY_LEVEL = "ENTRY_LEVEL", _("Entry Level")
    MID_LEVEL = "MID_LEVEL", _("Mid Level")
    SENIOR_LEVEL = "SENIOR_LEVEL", _("Senior Level")
    DIRECTOR = "DIRECTOR", _("Director")
    EXECUTIVE = "EXECUTIVE", _("Executive")


class SalaryPeriod(models.TextChoices):
    HOURLY = "HOURLY", _("Hourly")
    MONTHLY = "MONTHLY", _("Monthly")
    YEARLY = "YEARLY", _("Yearly")


class JobStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    PENDING_REVIEW = "PENDING_REVIEW", _("Pending Review")
    PUBLISHED = "PUBLISHED", _("Published")
    PAUSED = "PAUSED", _("Paused")
    CLOSED = "CLOSED", _("Closed")
    REJECTED = "REJECTED", _("Rejected")


class Job(UUIDTimeStampedModel):
    """
    Comprehensive job listing model representing vacancies published by companies.
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_jobs",
    )
    title = models.CharField(_("job title"), max_length=255, db_index=True)
    slug = models.SlugField(_("slug"), max_length=255, unique=True, db_index=True)
    description = models.TextField(_("job description"))
    responsibilities = models.TextField(_("responsibilities"), blank=True)
    requirements = models.TextField(_("requirements"), blank=True)
    category = models.ForeignKey(
        JobCategory,
        on_delete=models.PROTECT,
        related_name="jobs",
    )

    employment_type = models.CharField(
        _("employment type"),
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
        db_index=True,
    )
    workplace_type = models.CharField(
        _("workplace type"),
        max_length=20,
        choices=WorkplaceType.choices,
        default=WorkplaceType.ONSITE,
        db_index=True,
    )
    experience_level = models.CharField(
        _("experience level"),
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.MID_LEVEL,
        db_index=True,
    )

    location = models.CharField(_("city or office location"), max_length=255, db_index=True)
    country = models.CharField(_("country"), max_length=100, db_index=True)

    salary_min = models.DecimalField(
        _("minimum salary"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    salary_max = models.DecimalField(
        _("maximum salary"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    salary_currency = models.CharField(_("salary currency"), max_length=3, default="USD")
    salary_period = models.CharField(
        _("salary period"),
        max_length=20,
        choices=SalaryPeriod.choices,
        default=SalaryPeriod.YEARLY,
    )

    status = models.CharField(
        _("status"),
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.DRAFT,
        db_index=True,
    )

    published_at = models.DateTimeField(_("published at"), null=True, blank=True, db_index=True)
    application_deadline = models.DateTimeField(
        _("application deadline"), null=True, blank=True, db_index=True
    )

    class Meta:
        verbose_name = _("job listing")
        verbose_name_plural = _("job listings")
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["category", "employment_type", "workplace_type"]),
            models.Index(fields=["country", "location"]),
            models.Index(fields=["company", "status"]),
        ]

    def __str__(self):
        return f"{self.title} at {self.company.name}"

    def clean(self):
        super().clean()
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValidationError(
                    {"salary_min": _("Minimum salary cannot be greater than maximum salary.")}
                )

        if self.application_deadline and self.status == JobStatus.PUBLISHED:
            if self.application_deadline < timezone.now():
                raise ValidationError(
                    {
                        "application_deadline": _(
                            "Application deadline cannot be in the past for published jobs."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.company.name}-{self.title}")
            slug = base_slug
            counter = 1
            while Job.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if self.status == JobStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_accepting_applications(self) -> bool:
        """Determines whether the job is currently eligible to receive applications."""
        if self.status != JobStatus.PUBLISHED:
            return False
        if self.application_deadline and self.application_deadline < timezone.now():
            return False
        return True


class JobSkill(UUIDTimeStampedModel):
    """Associates a Skill with a Job listing."""

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="job_skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="job_skills",
    )
    is_required = models.BooleanField(_("is required"), default=True)

    class Meta:
        verbose_name = _("job skill")
        verbose_name_plural = _("job skills")
        unique_together = ("job", "skill")

    def __str__(self):
        return f"{self.job.title} - {self.skill.name} ({'Required' if self.is_required else 'Preferred'})"
