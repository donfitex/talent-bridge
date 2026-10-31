from urllib.parse import parse_qs, urlsplit

import pytest

from apps.common.models import ContactMessage
from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_contact_inbox_admin_only(client):
    item = ContactMessage.objects.create(
        name="Sender",
        email="sender@example.com",
        subject="Account & profile?",
        message="<script>bad</script>",
    )
    url = "/staff/contact-messages/"
    assert client.get(url).status_code == 302
    user = User.objects.create_user("candidate@example.com", "password")
    client.force_login(user)
    assert client.get(url).status_code == 403
    user.is_staff = True
    user.save()
    assert client.get(url).status_code == 403
    admin = User.objects.create_superuser("admin@example.com", "password")
    client.force_login(admin)
    response = client.get(url)
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    assert b"sender@example.com" in response.content
    assert b"<script>bad</script>" not in response.content
    parts = urlsplit(item.reply_url)
    assert parts.path == item.email
    assert parse_qs(parts.query)["subject"] == ["Re: Account & profile?"]
