from django.db.models import Count
from rest_framework import views
from apps.common.permissions import IsEmployerUser
from apps.common.responses import APIResponse
from apps.applications.access import employer_applications
from apps.jobs.models import Job
from apps.companies.models import EmployerMembership


class RecruitmentReportView(views.APIView):
    permission_classes = [IsEmployerUser]

    def get(self, request):
        applications = employer_applications(request.user)
        jobs = Job.objects.all()
        if not request.user.is_admin_user:
            jobs = jobs.filter(company_id__in=EmployerMembership.objects.filter(user=request.user, is_active=True).values("company_id"))
        return APIResponse(data={"jobs": jobs.count(), "published_jobs": jobs.filter(status="PUBLISHED").count(),
            "applications": applications.count(), "pipeline": list(applications.order_by().values("status").annotate(count=Count("id")))})
