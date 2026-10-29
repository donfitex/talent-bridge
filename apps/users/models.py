import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", _("Admin")
    EMPLOYER = "EMPLOYER", _("Employer")
    RECRUITER = "RECRUITER", _("Recruiter")
    CANDIDATE = "CANDIDATE", _("Candidate")


class UserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier for auth."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email).lower()
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_email_verified", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Custom user model for TalentBridge platform.
    Uses email as the unique identifier and supports multiple operational roles.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    role = models.CharField(
        _("primary role"),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CANDIDATE,
        db_index=True,
    )

    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into the admin site."),
    )
    is_active = models.BooleanField(
        _("active status"),
        default=True,
        help_text=_("Designates whether this user account should be treated as active."),
    )
    is_email_verified = models.BooleanField(
        _("email verified"),
        default=False,
        help_text=_("Designates whether the user has verified their email address."),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email", "role"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email

    def get_short_name(self):
        return self.first_name if self.first_name else self.email.split("@")[0]

    @property
    def is_candidate(self) -> bool:
        return self.role == UserRole.CANDIDATE

    @property
    def is_employer(self) -> bool:
        return self.role == UserRole.EMPLOYER

    @property
    def is_recruiter(self) -> bool:
        return self.role == UserRole.RECRUITER

    @property
    def is_admin_user(self) -> bool:
        return self.role == UserRole.ADMIN or self.is_superuser
