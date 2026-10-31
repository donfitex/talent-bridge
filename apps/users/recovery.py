"""Verify mailbox ownership through managed Neon OTP before local password recovery."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ValidationError


def auth_call(path, payload):
    base = settings.NEON_AUTH_BASE_URL.rstrip("/")
    if not base.startswith("https://"):
        raise ValidationError("Email recovery is not configured. Please contact support.")
    request = Request(
        base + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Origin": settings.FRONTEND_URL.rstrip("/")},
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError):
        raise ValidationError(
            "The email service could not complete this request. Check your code or try again shortly."
        ) from None


def send_code(email):
    auth_call("/email-otp/send-verification-otp", {"email": email.lower(), "type": "sign-in"})


def recover(email, code, password):
    from django.contrib.auth.password_validation import validate_password

    from apps.users.models import User

    email = email.lower()
    validate_password(password)
    result = auth_call("/sign-in/email-otp", {"email": email, "otp": code})
    identity = result.get("user") or {}
    if identity.get("email", "").lower() != email or not identity.get("emailVerified"):
        raise ValidationError("This verification code is invalid or expired.")
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        raise ValidationError("Unable to reset this account. Please contact support.")
    validate_password(password, user)
    user.set_password(password)
    user.is_email_verified = True
    user.save(update_fields=["password", "is_email_verified", "updated_at"])
