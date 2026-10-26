from rest_framework import viewsets, permissions, status, decorators
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.common.responses import APIResponse
from apps.common.permissions import IsEmployerUser
from apps.companies.models import EmployerMembership
from apps.jobs.models import Job, JobStatus
from apps.jobs.serializers import JobSerializer
from apps.jobs.services import JobManagementService


class EmployerJobViewSet(viewsets.ModelViewSet):
    """
    Dedicated viewset for employers and recruiters to manage company vacancies.
    """
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmployerUser]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, "is_admin_user", False):
            return Job.objects.all().select_related("company", "category").prefetch_related("job_skills__skill")

        company_ids = EmployerMembership.objects.filter(
            user=user, is_active=True
        ).values_list("company_id", flat=True)

        return (
            Job.objects.filter(company_id__in=company_ids)
            .select_related("company", "category")
            .prefetch_related("job_skills__skill")
        )

    def perform_create(self, serializer):
        company = serializer.validated_data["company"]
        JobManagementService.verify_employer_permission(self.request.user, company)
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        job = self.get_object()
        JobManagementService.verify_employer_permission(self.request.user, job.company)
        serializer.save()

    @decorators.action(detail=True, methods=["post"])
    def publish(self, request, id=None):
        job = self.get_object()
        updated_job = JobManagementService.publish_job(job, request.user)
        return APIResponse(
            data=JobSerializer(updated_job).data,
            message="Job listing published successfully.",
        )

    @decorators.action(detail=True, methods=["post"])
    def pause(self, request, id=None):
        job = self.get_object()
        updated_job = JobManagementService.pause_job(job, request.user)
        return APIResponse(
            data=JobSerializer(updated_job).data,
            message="Recruitment paused for this vacancy.",
        )

    @decorators.action(detail=True, methods=["post"])
    def close(self, request, id=None):
        job = self.get_object()
        updated_job = JobManagementService.close_job(job, request.user)
        return APIResponse(
            data=JobSerializer(updated_job).data,
            message="Vacancy closed. No new applications will be accepted.",
        )

    @decorators.action(detail=True, methods=["post"])
    def reopen(self, request, id=None):
        job = self.get_object()
        deadline = request.data.get("application_deadline")
        updated_job = JobManagementService.reopen_job(job, request.user, deadline)
        return APIResponse(
            data=JobSerializer(updated_job).data,
            message="Vacancy reopened successfully.",
        )

    @decorators.action(detail=True, methods=["post"])
    def duplicate(self, request, id=None):
        job = self.get_object()
        new_job = JobManagementService.duplicate_job(job, request.user)
        return APIResponse(
            data=JobSerializer(new_job).data,
            status_code=status.HTTP_201_CREATED,
            message="Job description cloned as a new draft.",
        )
