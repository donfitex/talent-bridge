import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.users.models import User
from apps.users.tokens import email_verification_token

logger = logging.getLogger("apps.users")


class UserService:
    """Service layer handling user lifecycle, authentication, and security workflows."""

    @staticmethod
    def register_user(
        email: str, password: str, role: str, first_name: str = "", last_name: str = ""
    ) -> User:
        """Creates a new user and generates initial activation / verification state."""
        user = User.objects.create_user(
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_email_verified=False,
        )
        UserService.send_email_verification(user)
        return user

    @staticmethod
    def send_email_verification(user: User) -> bool:
        """Sends an email verification link to user."""
        token = email_verification_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_link = f"{settings.FRONTEND_URL}/verify-email/?uid={uid}&token={token}"

        try:
            send_mail(
                subject="Verify your TalentBridge account",
                message=f"Welcome to TalentBridge!\n\nPlease verify your email address by clicking the link:\n{verification_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error("Failed to send verification email to %s: %s", user.email, e)
            return False

    @staticmethod
    @transaction.atomic
    def verify_email(uidb64: str, token: str) -> bool:
        """Validates verification token and activates email verification status."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.select_for_update().get(pk=uid, is_active=True)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UnicodeDecodeError,
            ValidationError,
            User.DoesNotExist,
        ):
            return False

        if email_verification_token.check_token(user, token):
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])
            return True
        return False

    @staticmethod
    def request_password_reset(email: str) -> bool:
        """Generates password reset token and dispatches reset instructions."""
        try:
            user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            # Prevent user enumeration by returning True silently
            return True

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{settings.FRONTEND_URL}/reset-password/?uid={uid}&token={token}"

        try:
            send_mail(
                subject="Reset your TalentBridge Password",
                message=f"Hello,\n\nYou requested a password reset. Click the link below to set a new password:\n{reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error("Failed to send password reset email to %s: %s", user.email, e)
            return False

    @staticmethod
    @transaction.atomic
    def confirm_password_reset(uidb64: str, token: str, new_password: str) -> bool:
        """Resets user password after token verification."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.select_for_update().get(pk=uid, is_active=True)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UnicodeDecodeError,
            ValidationError,
            User.DoesNotExist,
        ):
            return False

        if default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return True
        return False
