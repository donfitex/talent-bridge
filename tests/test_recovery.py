from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from apps.users.models import User
from apps.users.recovery import recover

pytestmark = pytest.mark.django_db


def test_recovery_requires_verified_matching_identity():
    user = User.objects.create_superuser("owner@example.com", "Old-password!123")
    for identity in [
        {"email": user.email, "emailVerified": False},
        {"email": "other@example.com", "emailVerified": True},
    ]:
        with patch("apps.users.recovery.auth_call", return_value={"user": identity}):
            with pytest.raises(ValidationError):
                recover(user.email, "123456", "Strong-new-password!789")
    user.refresh_from_db()
    assert user.check_password("Old-password!123")
    with patch(
        "apps.users.recovery.auth_call",
        return_value={"user": {"email": user.email, "emailVerified": True}},
    ):
        recover(user.email, "123456", "Strong-new-password!789")
    user.refresh_from_db()
    assert user.check_password("Strong-new-password!789")
    assert user.is_staff and user.is_superuser


def test_recovery_delivery_errors_are_visible(client, settings):
    settings.NEON_AUTH_BASE_URL = "https://auth.example.com/auth"
    with patch(
        "apps.users.recovery.send_code", side_effect=ValidationError("Email service unavailable")
    ):
        response = client.post("/accounts/password/reset/", {"email": "owner@example.com"})
    assert response.status_code == 200
    assert b"Email service unavailable" in response.content


def test_recovery_code_request(client, settings):
    settings.NEON_AUTH_BASE_URL = "https://auth.example.com/auth"
    with patch("apps.users.recovery.send_code") as send:
        response = client.post("/accounts/password/reset/", {"email": "owner@example.com"})
    send.assert_called_once_with("owner@example.com")
    assert response.url == "/accounts/password/code/"
    assert client.get(response.url).status_code == 200
