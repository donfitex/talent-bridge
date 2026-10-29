from drf_spectacular.utils import extend_schema
from rest_framework import decorators, permissions, viewsets

from apps.applications.models import ApplicationStatus, JobApplication
from apps.applications.serializers import JobApplicationSerializer
from apps.common.permissions import IsCandidateUser
from apps.common.responses import APIResponse


class CandidateApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Candidate API for inspecting application tracking history and withdrawing applications.
    GET /api/v1/applications/
    GET /api/v1/applications/{id}/
    POST /api/v1/applications/{id}/withdraw/
    """

    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsCandidateUser]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, "candidate_profile"):
            return JobApplication.objects.none()

        qs = (
            JobApplication.objects.filter(candidate=user.candidate_profile)
            .select_related("job", "job__company", "resume")
            .prefetch_related("history")
            .order_by("-created_at")
        )

        status_param = self.request.query_params.get("status")
        if status_param and status_param.upper() in ApplicationStatus.values:
            qs = qs.filter(status=status_param.upper())

        return qs

    @extend_schema(responses={200: JobApplicationSerializer})
    @decorators.action(detail=True, methods=["post"])
    def withdraw(self, request, id=None):
        application = self.get_object()

        from apps.applications.services import ApplicationWithdrawalService

        application = ApplicationWithdrawalService.withdraw(request.user, application.pk)

        return APIResponse(
            data=JobApplicationSerializer(application).data,
            message="Your job application has been successfully withdrawn.",
        )
