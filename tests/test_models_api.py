from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.applications.models import JobApplication
from apps.applications.services import ApplicationSubmissionService
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_model_constraints_and_history(recruitment):
    candidate, _, job, resume = recruitment
    with transaction.atomic(), pytest.raises(IntegrityError):
        User.objects.create(email=candidate.email)
    job.salary_min, job.salary_max = 200, 100
    with pytest.raises(ValidationError):
        job.full_clean()
    job.refresh_from_db()
    app = ApplicationSubmissionService.submit_application(candidate, job.pk, resume.pk)
    with transaction.atomic(), pytest.raises(IntegrityError):
        JobApplication.objects.create(candidate=app.candidate, job=job, resume=resume)
    record = app.history.get()
    with pytest.raises(ValueError):
        record.save()


def test_notification_retry(recruitment):
    candidate, _, _, _ = recruitment
    item = NotificationService.enqueue(candidate, "Update", "Message", "deduplicated")
    NotificationService.enqueue(candidate, "Update", "Message", "deduplicated")
    assert Notification.objects.count() == 1
    with patch("apps.notifications.services.send_mail", side_effect=OSError("offline")):
        assert NotificationService.dispatch() == 0
    item.refresh_from_db()
    assert item.attempts == 1 and item.sent_at is None
    assert NotificationService.dispatch() == 1


def test_public_search_validation_and_permissions(api_client, recruitment):
    _, employer, job, _ = recruitment
    assert api_client.get("/api/v1/jobs/?q=Engineer").status_code == 200
    assert api_client.get(f"/api/v1/jobs/{job.pk}/").status_code == 200
    api_client.force_authenticate(employer)
    response = api_client.patch(
        f"/api/v1/employer/jobs/{job.pk}/", {"salary_min": 200, "salary_max": 100}, format="json"
    )
    assert response.status_code == 400
    response = api_client.post(
        f"/api/v1/employer/jobs/{job.pk}/reopen/", {"application_deadline": "invalid"}
    )
    assert response.status_code == 400
    response = api_client.patch(
        f"/api/v1/employer/jobs/{job.pk}/",
        {"skill_ids": ["f4d7d9eb-4aa0-4a58-9ab7-a65f688bc054"]},
        format="json",
    )
    assert response.status_code == 400


def test_account_journey(api_client):
    cache.clear()
    response = api_client.post(
        "/api/v1/auth/register/candidate/",
        {
            "email": "NEW@EXAMPLE.COM",
            "password": "Complicated-Password-937",
            "password_confirm": "Complicated-Password-937",
            "first_name": "New",
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    assert (
        api_client.post(
            "/api/v1/auth/login/",
            {"email": "new@example.com", "password": "Complicated-Password-937"},
        ).status_code
        == 200
    )
    assert api_client.get("/api/v1/auth/me/").status_code == 200
    assert api_client.post("/api/v1/auth/logout/").status_code == 200
    assert api_client.get("/api/v1/auth/me/").status_code == 403
    cache.clear()
