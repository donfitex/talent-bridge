from apps.applications.models import JobApplication
from apps.companies.models import EmployerMembership


def employer_applications(user):
    qs = JobApplication.objects.select_related("job__company", "candidate__user", "resume")
    qs = qs.prefetch_related("history")
    if not user.is_authenticated:
        return qs.none()
    if user.is_admin_user:
        return qs
    return qs.filter(
        job__company_id__in=EmployerMembership.objects.filter(user=user, is_active=True).values(
            "company_id"
        )
    )
