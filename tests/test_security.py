import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.companies.models import Company, EmployerMembership
from apps.resumes.models import Resume
from apps.users.models import User
from apps.users.services import UserService
from apps.users.tokens import email_verification_token

pytestmark = pytest.mark.django_db


def test_private_resume_storage_and_role_guard(api_client, recruitment):
    candidate, employer, job, resume = recruitment
    api_client.force_authenticate(candidate)
    response = api_client.post(
        "/api/v1/resumes/",
        {"title": "Private CV", "file": SimpleUploadedFile("cv.pdf", b"%PDF-1.4\ncontent")},
        format="multipart",
    )
    assert response.status_code == 201, response.data
    saved = Resume.objects.get(pk=response.data["data"]["id"])
    assert "private_media" in str(saved.file.path)
    with pytest.raises(ValueError):
        _ = saved.file.url
    assert api_client.get(f"/api/v1/resumes/{saved.pk}/download/").status_code == 200
    api_client.force_authenticate(employer)
    assert api_client.get(f"/api/v1/resumes/{saved.pk}/download/").status_code == 403
    assert api_client.post("/api/v1/resumes/", {}, format="multipart").status_code == 403


def test_private_profiles_and_company_transfer(api_client, recruitment):
    candidate, employer, job, resume = recruitment
    candidate.candidate_profile.is_public = False
    candidate.candidate_profile.save()
    outsider = User.objects.create_user("outsider@example.com", role="EMPLOYER")
    api_client.force_authenticate(outsider)
    assert (
        api_client.get(f"/api/v1/candidates/{candidate.candidate_profile.pk}/").status_code == 404
    )
    other = Company.objects.create(name="Other")
    api_client.force_authenticate(employer)
    response = api_client.patch(
        f"/api/v1/employer/jobs/{job.pk}/", {"company": str(other.pk)}, format="json"
    )
    assert response.status_code == 403, response.data
    job.refresh_from_db()
    assert job.company != other


def test_company_member_cannot_escalate(api_client, recruitment):
    _, employer, job, _ = recruitment
    recruiter = User.objects.create_user("recruiter@example.com", role="RECRUITER")
    EmployerMembership.objects.create(user=recruiter, company=job.company)
    api_client.force_authenticate(recruiter)
    assert api_client.get(f"/api/v1/companies/{job.company_id}/members/").status_code == 200
    assert (
        api_client.post(
            f"/api/v1/companies/{job.company_id}/members/",
            {"email": employer.email, "role": "ADMIN"},
        ).status_code
        == 403
    )


def test_login_csrf_and_rate_limit(recruitment, settings):
    candidate, _, _, _ = recruitment
    cache.clear()
    client = Client(enforce_csrf_checks=True)
    assert (
        client.post(
            "/api/v1/auth/login/", {"email": candidate.email, "password": "strong-password"}
        ).status_code
        == 403
    )
    client.get("/api/v1/auth/csrf/")
    token = client.cookies["csrftoken"].value
    assert (
        client.post(
            "/api/v1/auth/login/",
            {"email": candidate.email, "password": "strong-password"},
            HTTP_X_CSRFTOKEN=token,
        ).status_code
        == 200
    )
    settings.AUTH_RATE_LIMIT = 1
    cache.clear()
    client.post("/api/v1/auth/login/", {})
    assert client.post("/api/v1/auth/login/", {}).status_code == 429
    cache.clear()


def test_verification_tokens_cannot_reset_password(recruitment):
    candidate, _, _, _ = recruitment
    uid = urlsafe_base64_encode(force_bytes(candidate.pk))
    token = email_verification_token.make_token(candidate)
    assert not UserService.confirm_password_reset(uid, token, "malicious-change")
    assert UserService.verify_email(uid, token)
    assert not UserService.verify_email(uid, token)
    reset = default_token_generator.make_token(candidate)
    assert UserService.confirm_password_reset(uid, reset, "new-password")


def test_malformed_reset_and_verification_tokens(api_client):
    assert (
        api_client.post(
            "/api/v1/auth/verify-email/", {"uid": "bm90LWEtdXVpZA", "token": "bad"}
        ).status_code
        == 400
    )
    response = api_client.post(
        "/api/v1/auth/password/reset/confirm/",
        {
            "uid": "bm90LWEtdXVpZA",
            "token": "bad",
            "new_password": "Complex-Pass-7239",
            "new_password_confirm": "Complex-Pass-7239",
        },
    )
    assert response.status_code == 400


def test_public_candidate_name_does_not_disclose_email(api_client, recruitment):
    candidate, employer, _, _ = recruitment
    api_client.force_authenticate(employer)
    response = api_client.get(f"/api/v1/candidates/{candidate.candidate_profile.pk}/")
    assert response.status_code == 200
    assert candidate.email not in str(response.data)
