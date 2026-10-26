from rest_framework import views, permissions, status
from drf_spectacular.utils import extend_schema

from apps.common.responses import APIResponse
from apps.applications.services import ApplicationSubmissionService
from apps.applications.serializers import (
    ApplicationSubmissionSerializer,
    JobApplicationSerializer,
)


class JobApplicationSubmissionView(views.APIView):
    """
    POST /api/v1/jobs/{id}/apply/
    Allows an authenticated candidate to apply for a published vacancy.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=ApplicationSubmissionSerializer,
        responses={201: JobApplicationSerializer},
        description="Submit a job application for the specified job listing.",
    )
    def post(self, request, id):
        serializer = ApplicationSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        application = ApplicationSubmissionService.submit_application(
            user=request.user,
            job_id=id,
            resume_id=serializer.validated_data["resume_id"],
            cover_letter=serializer.validated_data.get("cover_letter", ""),
        )

        return APIResponse(
            data=JobApplicationSerializer(application).data,
            status_code=status.HTTP_201_CREATED,
            message="Your job application has been successfully submitted.",
        )
