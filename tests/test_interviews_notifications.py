from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.applications.services import ApplicationSubmissionService, ApplicationTransitionService
from apps.interviews.models import Interview
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService

pytestmark = pytest.mark.django_db


def test_scheduling_overlap_privacy_and_cancellation(api_client, recruitment):
    candidate, employer, job, resume = recruitment
    application = ApplicationSubmissionService.submit_application(candidate, job.pk, resume.pk)
    for target in ["UNDER_REVIEW", "SHORTLISTED", "INTERVIEW"]:
        ApplicationTransitionService.transition(employer, application.pk, target)
    api_client.force_authenticate(employer)
    start = timezone.now() + timedelta(hours=2)
    data = {
        "application": str(application.pk),
        "interviewer": str(employer.pk),
        "starts_at": start.isoformat(),
        "ends_at": (start + timedelta(hours=1)).isoformat(),
        "location": "Lagos office",
    }
    response = api_client.post("/api/v1/interviews/", data, format="json")
    assert response.status_code == 201, response.data
    pk = response.data["id"]
    assert api_client.post("/api/v1/interviews/", data, format="json").status_code == 409
    assert (
        api_client.patch(f"/api/v1/interviews/{pk}/", {"feedback": "Internal notes"}).status_code
        == 200
    )
    api_client.force_authenticate(candidate)
    response = api_client.get(f"/api/v1/interviews/{pk}/")
    assert response.status_code == 200
    assert "feedback" not in response.data
    assert api_client.patch(f"/api/v1/interviews/{pk}/", {"status": "CANCELLED"}).status_code == 403
    api_client.force_authenticate(employer)
    assert api_client.patch(f"/api/v1/interviews/{pk}/", {"status": "CANCELLED"}).status_code == 200
    assert Interview.objects.get(pk=pk).status == "CANCELLED"


def test_notification_outbox_retry_and_owner(api_client, recruitment, settings):
    candidate, employer, job, resume = recruitment
    ApplicationSubmissionService.submit_application(candidate, job.pk, resume.pk)
    assert Notification.objects.count() == 2
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    assert NotificationService.dispatch() == 2
    assert len(mail.outbox) == 2
    assert NotificationService.dispatch() == 0
    item = Notification.objects.filter(user=candidate).first()
    api_client.force_authenticate(employer)
    assert api_client.get(f"/api/v1/notifications/{item.pk}/").status_code == 404
    api_client.force_authenticate(candidate)
    assert api_client.post(f"/api/v1/notifications/{item.pk}/read/").status_code == 200
    api_client.force_authenticate(employer)
    assert api_client.get("/api/v1/employer/reports/").data["data"]["applications"] == 1


def test_withdrawal_cancels_scheduled_interviews(recruitment):
    from apps.applications.services import ApplicationWithdrawalService
    from apps.interviews.services import InterviewService

    candidate, employer, job, resume = recruitment
    application = ApplicationSubmissionService.submit_application(candidate, job.pk, resume.pk)
    for target in ["UNDER_REVIEW", "SHORTLISTED", "INTERVIEW"]:
        ApplicationTransitionService.transition(employer, application.pk, target)
    start = timezone.now() + timedelta(days=1)
    item = InterviewService.schedule(
        employer,
        {
            "application": application,
            "interviewer": employer,
            "starts_at": start,
            "ends_at": start + timedelta(hours=1),
            "location": "Office",
        },
    )
    ApplicationWithdrawalService.withdraw(candidate, application.pk)
    item.refresh_from_db()
    assert item.status == "CANCELLED"
