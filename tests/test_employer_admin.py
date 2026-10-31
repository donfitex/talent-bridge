import pytest

from apps.companies.models import Company, CompanySize
from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_company_size_defaults_unknown():
    assert Company(name="New company").company_size == CompanySize.UNKNOWN


def test_employer_approval_and_deactivation(client):
    owner = User.objects.create_superuser("owner@example.com", "password")
    employer = User.objects.create_user("employer@example.com", "password", role="EMPLOYER")
    client.force_login(owner)
    assert b"Awaiting administrator approval" in client.get("/admin/").content
    url = "/admin/users/employeraccount/"
    assert (
        b"employer@example.com"
        in client.get(url + "?employer_approved__exact=0&is_active__exact=1").content
    )

    def action(name):
        assert (
            client.post(url, {"action": name, "_selected_action": [str(employer.pk)]}).status_code
            == 302
        )
        employer.refresh_from_db()

    action("approve_employers")
    assert employer.employer_approved
    action("deactivate_employers")
    assert not employer.is_active and not employer.employer_approved
    action("approve_employers")
    assert not employer.employer_approved
    action("reactivate_employers")
    assert employer.is_active and not employer.employer_approved
    client.logout()
    assert not client.login(username=employer.email, password="wrong")
