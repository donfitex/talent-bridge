from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, views

from apps.applications.access import employer_applications
from apps.common.permissions import IsEmployerUser
from apps.common.responses import APIResponse
from apps.companies.models import EmployerMembership
from apps.jobs.models import Job


class PipelineCountSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class RecruitmentReportSerializer(serializers.Serializer):
    jobs = serializers.IntegerField()
    published_jobs = serializers.IntegerField()
    applications = serializers.IntegerField()
    pipeline = PipelineCountSerializer(many=True)


class RecruitmentReportView(views.APIView):
    permission_classes = [IsEmployerUser]

    @extend_schema(responses=RecruitmentReportSerializer)
    def get(self, request):
        applications = employer_applications(request.user)
        jobs = Job.objects.all()
        if not request.user.is_admin_user:
            jobs = jobs.filter(
                company_id__in=EmployerMembership.objects.filter(
                    user=request.user, is_active=True
                ).values("company_id")
            )
        return APIResponse(
            data={
                "jobs": jobs.count(),
                "published_jobs": jobs.filter(status="PUBLISHED").count(),
                "applications": applications.count(),
                "pipeline": list(
                    applications.order_by().values("status").annotate(count=Count("id"))
                ),
            }
        )
