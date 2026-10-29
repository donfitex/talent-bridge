from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connection

from apps.applications.models import JobApplication
from apps.applications.services import ApplicationSubmissionService
from apps.common.exceptions import TalentBridgeAPIException
from apps.users.models import User

pytestmark = pytest.mark.django_db(transaction=True)


def test_simultaneous_duplicate_submission(recruitment):
    if connection.vendor != "postgresql":
        pytest.skip("Real PostgreSQL row locks are required for this test.")
    candidate, _, job, resume = recruitment
    barrier = Barrier(4)

    def submit(_):
        close_old_connections()
        try:
            user = User.objects.get(pk=candidate.pk)
            barrier.wait(timeout=20)
            try:
                ApplicationSubmissionService.submit_application(user, job.pk, resume.pk)
                return 201
            except TalentBridgeAPIException as exc:
                return exc.status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(submit, range(4)))
    assert results.count(201) == 1
    assert results.count(409) == 3
    assert JobApplication.objects.filter(job=job, candidate__user=candidate).count() == 1
