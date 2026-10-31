from io import StringIO
from unittest.mock import patch

import pandas as pd
import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command

from apps.companies.models import Company
from apps.jobs.external import import_job
from apps.jobs.models import Job

pytestmark = pytest.mark.django_db
ROW = {
    "site": "indeed",
    "title": "Engineer",
    "company": "Example",
    "job_url": "https://uk.indeed.com/viewjob?jk=123&tracking=x",
    "description": float("nan"),
    "location": float("nan"),
}


def test_import_deduplicates_and_requires_review():
    assert import_job(ROW, "UK", "Engineering")
    assert not import_job(
        {**ROW, "job_url": "https://www.indeed.com/viewjob?jk=123"}, "UK", "Engineering"
    )
    job = Job.objects.get()
    assert job.status == "PENDING_REVIEW"
    assert job.source_url == "https://www.indeed.com/viewjob?jk=123"
    assert "Originally posted on Indeed" in job.description
    assert "nan" not in job.description
    assert not job.is_accepting_applications
    assert not job.company.is_verified


def test_dry_run_and_invalid_url():
    assert import_job(ROW, "UK", "Engineering", dry_run=True)
    assert not Job.objects.exists() and not Company.objects.exists()
    with pytest.raises(ValidationError):
        import_job({**ROW, "job_url": "javascript:alert(1)"}, "UK", "Engineering")


def test_command_reports_real_counts():
    output = StringIO()
    with patch(
        "apps.jobs.management.commands.sync_external_jobs.scrape_jobs",
        return_value=pd.DataFrame([ROW, ROW]),
    ):
        call_command("sync_external_jobs", stdout=output)
    assert "Added for admin review: 1; duplicates: 1; invalid: 0" in output.getvalue()


def test_full_content_and_duplicate_enrichment():
    row = {
        **ROW,
        "description": "Build useful software.\n## Responsibilities\n- Build APIs\n## Requirements\n- Python experience\n## Benefits\n- Flexible hours",
    }
    assert import_job(ROW, "UK", "Engineering")
    assert not import_job(row, "UK", "Engineering")
    job = Job.objects.get()
    assert job.description.startswith("Build useful software.")
    assert job.responsibilities == "- Build APIs"
    assert job.requirements == "- Python experience"
    assert "Flexible hours" not in job.requirements
    assert job.source_url.startswith("https://www.indeed.com/viewjob?")
    assert not import_job({**row, "requirements": "Changed source"}, "UK", "Engineering")
    job.refresh_from_db()
    assert job.requirements == "- Python experience"


def test_company_metadata_and_public_profile(client):
    row = {
        **ROW,
        "company_description": "We build useful software.",
        "company_logo": "https://cdn.example.com/logo.png",
        "company_industry": "Software",
        "company_url_direct": "https://example.com",
    }
    assert import_job(row, "UK", "Engineering")
    company = Job.objects.get().company
    assert company.description == "We build useful software."
    assert company.display_logo_url == "https://cdn.example.com/logo.png"
    response = client.get(f"/companies/{company.slug}/")
    assert response.status_code == 200
    assert b"We build useful software." in response.content
    assert b"cdn.example.com/logo.png" in response.content
    assert not import_job(
        {**row, "company_description": "Overwrite", "company_logo": "javascript:bad"},
        "UK",
        "Engineering",
    )
    company.refresh_from_db()
    assert company.description == "We build useful software."


def test_import_preserves_published_status(client):
    from apps.users.models import User

    import_job(ROW, "UK", "Engineering")
    job = Job.objects.get()
    user = User.objects.create_superuser("publisher@example.com", "password")
    client.force_login(user)
    response = client.post(
        "/admin/jobs/job/", {"action": "publish_selected", "_selected_action": [str(job.pk)]}
    )
    assert response.status_code == 302
    job.refresh_from_db()
    assert job.status == "PUBLISHED" and job.published_at
    assert not import_job(ROW, "UK", "Engineering")
    job.refresh_from_db()
    assert job.status == "PUBLISHED"
    assert b"Published" in client.get(f"/jobs/{job.pk}/").content


def test_nigeria_catalog_and_sharding():
    from apps.jobs.catalog import SEARCHES, classify

    assert len(SEARCHES) >= 40
    assert classify("Nurse") == "Healthcare"
    assert classify("Driver") == "Transport and Driving"
    groups = [
        {name for index, name in enumerate(SEARCHES) if index % 8 == shard} for shard in range(8)
    ]
    assert set.union(*groups) == set(SEARCHES)
    assert sum(map(len, groups)) == len(SEARCHES)


def test_local_structured_data():
    from apps.jobs.local_sources import structured_jobs

    jobs = list(
        structured_jobs(
            {"@graph": [{"@type": "JobPosting", "title": "Teacher"}, {"@type": "Organization"}]}
        )
    )
    assert len(jobs) == 1 and jobs[0]["title"] == "Teacher"


def test_local_source_url_validation():
    from apps.jobs.external import canonical_url

    assert (
        canonical_url("https://www.myjobmag.com/job/teacher?tracking=yes", "myjobmag")
        == "https://www.myjobmag.com/job/teacher"
    )
    with pytest.raises(ValidationError):
        canonical_url("https://myjobmag.com.evil.example/job/x", "myjobmag")
