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
