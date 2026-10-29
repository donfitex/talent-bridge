import pytest

from apps.applications.services import ApplicationSubmissionService
from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_public_pages_and_candidate_journey(client, recruitment):
    candidate, employer, job, resume = recruitment
    for url in [
        "/",
        "/jobs/",
        "/companies/",
        f"/jobs/{job.pk}/",
        "/accounts/login/",
        "/accounts/register/",
    ]:
        response = client.get(url)
        assert response.status_code == 200, url
    client.force_login(candidate)
    assert client.get("/candidate/dashboard/").status_code == 200
    assert client.get("/candidate/profile/").status_code == 200
    assert client.get("/candidate/resumes/").status_code == 200
    assert client.get(f"/jobs/{job.pk}/apply/").status_code == 200
    response = client.post(
        f"/jobs/{job.pk}/apply/", {"resume": str(resume.pk), "cover_letter": "Hello"}
    )
    assert response.status_code == 302
    app = candidate.candidate_profile.applications.get()
    assert client.post(f"/candidate/applications/{app.pk}/withdraw/").status_code == 302
    app.refresh_from_db()
    assert app.status == "WITHDRAWN"
    assert client.get("/employer/dashboard/").status_code == 403


def test_employer_web_and_admin(client, recruitment):
    candidate, employer, job, resume = recruitment
    app = ApplicationSubmissionService.submit_application(candidate, job.pk, resume.pk)
    client.force_login(employer)
    for url in [
        "/employer/dashboard/",
        "/employer/jobs/new/",
        "/employer/company/",
        f"/employer/jobs/{job.pk}/edit/",
        f"/employer/applications/{app.pk}/",
        f"/employer/applications/{app.pk}/interview/",
    ]:
        assert client.get(url).status_code == 200, url
    assert client.post(f"/employer/jobs/{job.pk}/pause/").status_code == 302
    assert client.post(f"/employer/jobs/{job.pk}/publish/").status_code == 302
    admin = User.objects.create_superuser("admin@example.com", "password")
    client.force_login(admin)
    for url in [
        "/admin/",
        "/admin/users/user/",
        "/admin/jobs/job/",
        "/admin/applications/applicationstatushistory/",
    ]:
        assert client.get(url).status_code == 200, url
