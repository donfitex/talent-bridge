from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.common.models import UUIDTimeStampedModel


class CompanyVerificationStatus(models.TextChoices):
    UNVERIFIED = "UNVERIFIED", _("Unverified")
    PENDING = "PENDING", _("Pending Verification")
    VERIFIED = "VERIFIED", _("Verified")
    REJECTED = "REJECTED", _("Rejected")
    SUSPENDED = "SUSPENDED", _("Suspended")


class CompanySize(models.TextChoices):
    SIZE_1_10 = "1-10", _("1-10 employees")
    SIZE_11_50 = "11-50", _("11-50 employees")
    SIZE_51_200 = "51-200", _("51-200 employees")
    SIZE_201_500 = "201-500", _("201-500 employees")
    SIZE_501_1000 = "501-1000", _("501-1000 employees")
    SIZE_1000_PLUS = "1000+", _("1000+ employees")


class Company(UUIDTimeStampedModel):
    """
    Organization profile representing an employer hiring on TalentBridge.
    """

    name = models.CharField(_("company name"), max_length=255, db_index=True)
    slug = models.SlugField(_("slug"), max_length=255, unique=True, db_index=True)
    description = models.TextField(_("description"), blank=True)
    industry = models.CharField(_("industry"), max_length=100, blank=True, db_index=True)
    company_size = models.CharField(
        _("company size"),
        max_length=20,
        choices=CompanySize.choices,
        default=CompanySize.SIZE_11_50,
    )
    website = models.URLField(_("website URL"), max_length=255, blank=True)
    logo = models.ImageField(_("company logo"), upload_to="company_logos/", blank=True, null=True)
    location = models.CharField(_("location"), max_length=255, blank=True)
    country = models.CharField(_("country"), max_length=100, blank=True, db_index=True)

    verification_status = models.CharField(
        _("verification status"),
        max_length=20,
        choices=CompanyVerificationStatus.choices,
        default=CompanyVerificationStatus.UNVERIFIED,
        db_index=True,
    )

    class Meta:
        verbose_name = _("company")
        verbose_name_plural = _("companies")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name", "verification_status"]),
            models.Index(fields=["industry", "country"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Company.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_verified(self) -> bool:
        return self.verification_status == CompanyVerificationStatus.VERIFIED


class EmployerRole(models.TextChoices):
    OWNER = "OWNER", _("Owner")
    ADMIN = "ADMIN", _("Admin")
    RECRUITER = "RECRUITER", _("Recruiter")


class EmployerMembership(UUIDTimeStampedModel):
    """
    Membership association linking a User to a Company with designated roles.
    Supports multi-recruiter teams per company.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employer_memberships",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        _("membership role"),
        max_length=20,
        choices=EmployerRole.choices,
        default=EmployerRole.RECRUITER,
    )
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _("employer membership")
        verbose_name_plural = _("employer memberships")
        unique_together = ("user", "company")
        indexes = [
            models.Index(fields=["user", "company", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.company.name} ({self.role})"
