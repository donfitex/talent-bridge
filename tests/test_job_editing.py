import pytest

from apps.common.templatetags.job_content import rich_content
from apps.jobs.models import Job, JobCategory

pytestmark = pytest.mark.django_db


def test_defaults_and_safe_formatting():
    job = Job()
    assert job.experience_level == "UNSPECIFIED" and job.salary_currency == "NGN"
    html = str(
        rich_content(
            '<h2>Requirements</h2><ul><li><strong>Python</strong></li></ul><img src=x onerror=alert(1)><a href="javascript:bad">bad</a>'
        )
    )
    assert "<li><strong>Python</strong></li>" in html
    assert "onerror" not in html and "javascript:" not in html
    assert "<li>Python</li>" in str(rich_content("- Python\n- Django"))


def test_multiple_categories_and_external_apply(client, api_client, recruitment):
    _, employer, job, _ = recruitment
    second = JobCategory.objects.create(name="Extra category")
    api_client.force_authenticate(employer)
    endpoint = f"/api/v1/employer/jobs/{job.pk}/"
    response = api_client.patch(
        endpoint,
        {
            "additional_categories": [str(second.pk)],
            "external_apply_url": "https://careers.example.com/job/123",
            "how_to_apply": "<p>Apply online.</p>",
        },
        format="json",
    )
    assert response.status_code == 200, response.data
    job.refresh_from_db()
    assert job.additional_categories.filter(pk=second.pk).exists()
    assert job.status == "PUBLISHED"
    client.force_login(employer)
    assert client.get(f"/employer/jobs/{job.pk}/edit/").status_code == 200
    assert job.title.encode() in client.get(f"/jobs/?category={second.slug}").content
    html = client.get(f"/jobs/{job.pk}/").content.decode()
    assert "careers.example.com/job/123" in html
    assert "Apply online." in html
    assert "Share this job" in html and "WhatsApp" in html


def test_publication_dates_and_employer_status(client, recruitment):
    _, employer, job, _ = recruitment
    assert "Published:" in client.get(f"/jobs/{job.pk}/").content.decode()
    assert "Published:" in client.get("/jobs/").content.decode()
    client.force_login(employer)
    html = client.get("/employer/dashboard/").content.decode()
    assert "bg-success" in html and "Published</button>" in html
    assert "Closing date:" in html


def test_external_fields_have_backward_compatible_database_defaults():
    assert Job._meta.get_field("external_apply_url").db_default == ""
    assert Job._meta.get_field("how_to_apply").db_default == ""
