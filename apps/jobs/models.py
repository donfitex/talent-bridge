import uuid
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from apps.common.models import UUIDTimeStampedModel


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
