from datetime import timedelta

import pytest
from django.utils import timezone

from apps.applications.models import ApplicationStatus
from apps.applications.services import ApplicationSubmissionService
from apps.candidates.models import CandidateProfile
from apps.companies.models import Company, EmployerMembership
from apps.jobs.models import Job, JobCategory, JobStatus
from apps.resumes.models import Resume
from apps.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def recruitment():
    candidate = User.objects.create_user("candidate@example.com", "strong-password")
    employer = User.objects.create_user("employer@example.com", "strong-password", role="EMPLOYER")
    profile = CandidateProfile.objects.create(user=candidate)
    company = Company.objects.create(name="Bridge")
    EmployerMembership.objects.create(user=employer, company=company, role="OWNER")
    category = JobCategory.objects.create(name="Engineering")
    job = Job.objects.create(
        company=company,
        created_by=employer,
        category=category,
        title="Engineer",
        description="Build reliable systems",
        location="Lagos",
        country="Nigeria",
        status=JobStatus.PUBLISHED,
        application_deadline=timezone.now() + timedelta(days=7),
    )
    resume = Resume.objects.create(
        candidate=profile,
        title="CV",
        file="resumes/example.pdf",
        original_filename="cv.pdf",
        file_type="application/pdf",
        file_size=100,
    )
    return candidate, employer, job, resume


def test_submit_withdraw_and_reapply(api_client, recruitment):
    candidate, _, job, resume = recruitment
    api_client.force_authenticate(candidate)
    response = api_client.post(f"/api/v1/jobs/{job.id}/apply/", {"resume_id": str(resume.id)})
    assert response.status_code == 201
    application_id = response.data["data"]["id"]
    assert "/download/" in response.data["data"]["resume_url"]
    assert (
        api_client.post(f"/api/v1/jobs/{job.id}/apply/", {"resume_id": str(resume.id)}).status_code
        == 409
    )
    assert api_client.get(f"/api/v1/applications/{application_id}/").status_code == 200
    assert api_client.post(f"/api/v1/applications/{application_id}/withdraw/").status_code == 200
    assert api_client.post(f"/api/v1/applications/{application_id}/withdraw/").status_code == 409
    ApplicationSubmissionService.submit_application(candidate, job.id, resume.id)


def test_application_ownership_and_roles(api_client, recruitment):
    candidate, employer, job, resume = recruitment
    application = ApplicationSubmissionService.submit_application(candidate, job.id, resume.id)
    stranger = User.objects.create_user("stranger@example.com", "strong-password")
    api_client.force_authenticate(stranger)
    assert api_client.get(f"/api/v1/applications/{application.id}/").status_code == 404
    assert (
        api_client.post(f"/api/v1/jobs/{job.id}/apply/", {"resume_id": str(resume.id)}).status_code
        == 400
    )
    api_client.force_authenticate(employer)
    assert (
        api_client.post(f"/api/v1/jobs/{job.id}/apply/", {"resume_id": str(resume.id)}).status_code
        == 403
    )


def test_deadline_and_hired_withdrawal(api_client, recruitment):
    candidate, _, job, resume = recruitment
    application = ApplicationSubmissionService.submit_application(candidate, job.id, resume.id)
    application.status = ApplicationStatus.HIRED
    application.save()
    api_client.force_authenticate(candidate)
    assert api_client.post(f"/api/v1/applications/{application.id}/withdraw/").status_code == 409
    Job.objects.filter(pk=job.pk).update(application_deadline=timezone.now() - timedelta(seconds=1))
    with pytest.raises(Exception, match="expired"):
        ApplicationSubmissionService.submit_application(candidate, job.id, resume.id)


def test_employer_pipeline_and_history(api_client, recruitment):
    from apps.applications.models import ApplicationStatusHistory

    candidate, employer, job, resume = recruitment
    application = ApplicationSubmissionService.submit_application(candidate, job.id, resume.id)
    api_client.force_authenticate(employer)
    url = f"/api/v1/employer/applications/{application.pk}/transition/"
    assert api_client.post(url, {"status": "HIRED"}).status_code == 409
    for target in ["UNDER_REVIEW", "SHORTLISTED", "INTERVIEW", "OFFERED", "HIRED"]:
        assert api_client.post(url, {"status": target}).status_code == 200
    assert ApplicationStatusHistory.objects.filter(application=application).count() == 6
    assert api_client.get("/api/v1/employer/applications/export/").status_code == 200
    stranger = User.objects.create_user("other-employer@example.com", role="EMPLOYER")
    api_client.force_authenticate(stranger)
    assert api_client.post(url, {"status": "REJECTED"}).status_code == 404
    assert api_client.get(f"/api/v1/employer/applications/{application.pk}/").status_code == 404
