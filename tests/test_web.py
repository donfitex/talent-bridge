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


@pytest.mark.parametrize("role", ["CANDIDATE", "EMPLOYER"])
def test_registration_validation_and_login(client, role):
    payload = {
        "email": f"{role.lower()}@example.com",
        "first_name": "Test",
        "last_name": "Account",
        "role": role,
        "password": "Secure-test-Pass!789",
        "password_confirm": "wrong",
    }
    response = client.post("/accounts/register/", payload)
    assert response.status_code == 200
    assert "Passwords do not match" in response.content.decode()
    payload["password_confirm"] = payload["password"]
    assert client.post("/accounts/register/", payload).status_code == 302
    user = User.objects.get(email=payload["email"])
    assert user.role == role
    assert not user.is_staff
    assert (
        client.post(
            "/accounts/login/", {"username": user.email, "password": payload["password"]}
        ).status_code
        == 302
    )
    assert client.get("/dashboard/").status_code == 302
    assert client.get("/admin/").status_code == 302


def test_contact_inbox_and_public_footer(client):
    from apps.common.models import ContactMessage

    response = client.get("/")
    html = response.content.decode()
    assert "Production-Ready" not in html
    assert "OpenAPI Schema" not in html
    assert 'href="/health/"' not in html
    assert 'href="/contact/"' in html
    assert client.get("/contact/").status_code == 200
    data = {
        "name": "Visitor",
        "email": "visitor@example.com",
        "subject": "Account help",
        "message": "Please help with my profile.",
    }
    assert client.post("/contact/", {**data, "website": "spam"}).status_code == 200
    assert not ContactMessage.objects.exists()
    assert client.post("/contact/", data).status_code == 302
    assert ContactMessage.objects.get().subject == "Account help"
    html = client.get("/accounts/register/").content.decode()
    assert "Forgot your password?" not in html
    assert "Create an account</a>" not in html.split("<footer", 1)[0]


def test_every_model_has_admin_controls(client, recruitment):
    from django.apps import apps
    from django.contrib import admin
    from django.urls import reverse

    user = User.objects.create_superuser("full-admin@example.com", "password")
    client.force_login(user)
    for model in apps.get_models():
        if model._meta.app_config.name.startswith("apps."):
            assert model in admin.site._registry, model
            assert (
                client.get(
                    reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")
                ).status_code
                == 200
            )

            for obj in model.objects.all()[:2]:
                response = client.get(
                    reverse(
                        f"admin:{model._meta.app_label}_{model._meta.model_name}_change",
                        args=[obj.pk],
                    )
                )
                assert response.status_code == 200, model
