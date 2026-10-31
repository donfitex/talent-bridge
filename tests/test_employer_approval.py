import pytest

from apps.jobs.services import JobManagementService
from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_employer_requires_admin_approval(client, api_client, recruitment):
    _, employer, job, _ = recruitment
    employer.employer_approved = False
    employer.save(update_fields=["employer_approved"])
    client.force_login(employer)
    assert client.get("/employer/jobs/new/").url == "/employer/dashboard/"
    assert b"awaiting administrator approval" in client.get("/employer/dashboard/").content
    api_client.force_authenticate(employer)
    endpoint = f"/api/v1/employer/jobs/{job.pk}/"
    assert api_client.patch(endpoint, {"title": "Bypass approval"}).status_code == 403
    assert api_client.post(endpoint + "publish/").status_code == 403
    with pytest.raises(Exception, match="awaiting administrator approval"):
        JobManagementService.duplicate_job(job, employer)
    employer.employer_approved = True
    employer.save(update_fields=["employer_approved"])
    assert api_client.post(endpoint + "publish/").status_code == 200
    employer.employer_approved = False
    employer.save(update_fields=["employer_approved"])
    assert api_client.post(endpoint + "reopen/").status_code == 403


def test_new_employer_is_not_approved():
    user = User.objects.create_user("pending@example.com", "password", role="EMPLOYER")
    assert not user.employer_approved


def test_company_creation_requires_approval(client, api_client, recruitment):
    from apps.companies.models import Company

    _, employer, _, _ = recruitment
    employer.employer_approved = False
    employer.save(update_fields=["employer_approved"])
    client.force_login(employer)
    api_client.force_authenticate(employer)
    count = Company.objects.count()
    assert client.get("/employer/company/").url == "/employer/dashboard/"
    assert client.post("/employer/company/", {"name": "Blocked"}).status_code == 302
    assert api_client.post("/api/v1/companies/", {"name": "Blocked"}).status_code == 403
    assert Company.objects.count() == count
    employer.employer_approved = True
    employer.save(update_fields=["employer_approved"])
    assert client.get("/employer/company/").status_code == 200
    assert api_client.post("/api/v1/companies/", {"name": "Approved company"}).status_code == 201
