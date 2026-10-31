from datetime import timedelta

import pytest
from django.utils import timezone

from apps.applications.models import ExternalApplication

pytestmark = pytest.mark.django_db


def test_external_confirmation_is_private_and_idempotent(client, recruitment):
    candidate, employer, job, _ = recruitment
    job.source_url = "https://www.indeed.com/viewjob?jk=tracking"
    job.save()
    url = f"/jobs/{job.pk}/external/confirm/"
    assert client.post(url, {"answer": "yes"}).status_code == 302
    assert not ExternalApplication.objects.exists()
    client.force_login(candidate)
    assert client.post(url, {"answer": "no"}).status_code == 302
    assert not ExternalApplication.objects.exists()
    for _ in range(2):
        assert client.post(url, {"answer": "yes"}).status_code == 302
    assert ExternalApplication.objects.count() == 1
    assert b"already applied for this role" in client.get(f"/jobs/{job.pk}/").content
    assert b"Self-reported" in client.get("/candidate/dashboard/").content
    client.force_login(employer)
    assert client.post(url, {"answer": "yes"}).status_code == 403
    assert b"already applied for this role" not in client.get(f"/jobs/{job.pk}/").content


def test_public_expiry_and_no_public_publication_badge(client, recruitment):
    _, _, job, _ = recruitment
    type(job).objects.filter(pk=job.pk).update(
        application_deadline=timezone.now() - timedelta(days=1)
    )
    for path in ["/jobs/", f"/jobs/{job.pk}/"]:
        html = client.get(path).content.decode()
        assert "This job offer has expired." in html
        assert "text-danger" in html
        assert ">Published</span>" not in html
