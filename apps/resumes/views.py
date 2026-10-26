from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, decorators
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema

from apps.common.responses import APIResponse
from apps.common.exceptions import TalentBridgeAPIException
from apps.candidates.models import CandidateProfile
from apps.resumes.models import Resume
from apps.resumes.serializers import ResumeSerializer, ResumeUploadSerializer
from apps.resumes.services import ResumeService


class ResumeViewSet(viewsets.ModelViewSet):
    """
    Candidate resume management and secure file handling endpoint.
    """
    serializer_class = ResumeSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, "candidate_profile"):
            return Resume.objects.none()
        return Resume.objects.filter(candidate=user.candidate_profile)

    @extend_schema(request=ResumeUploadSerializer, responses={201: ResumeSerializer})
    def create(self, request, *args, **kwargs):
        candidate, _ = CandidateProfile.objects.get_or_create(user=request.user)
        serializer = ResumeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = serializer.validated_data["file"]
        title = serializer.validated_data.get("title") or file_obj.name
        is_default = serializer.validated_data.get("is_default", False)

        resume = ResumeService.upload_resume(
            candidate=candidate,
            file_obj=file_obj,
            title=title,
            is_default=is_default,
        )

        return APIResponse(
            data=ResumeSerializer(resume, context={"request": request}).data,
            status_code=status.HTTP_201_CREATED,
            message="Resume uploaded successfully.",
        )

    @decorators.action(detail=True, methods=["post"])
    def default(self, request, id=None):
        resume = self.get_object()
        resume.set_as_default()
        return APIResponse(
            data=ResumeSerializer(resume, context={"request": request}).data,
            message="Resume set as default successfully.",
        )

    @decorators.action(detail=True, methods=["get"])
    def download(self, request, id=None):
        resume = get_object_or_404(Resume, id=id)

        if not ResumeService.authorize_download(resume, request.user):
            raise TalentBridgeAPIException(
                detail="You do not have permission to access or download this resume.",
                code="UNAUTHORIZED_RESUME_ACCESS",
                status_code=403,
            )

        if not resume.file or not resume.file.storage.exists(resume.file.name):
            raise Http404("Resume file not found on storage server.")

        response = FileResponse(resume.file.open("rb"), content_type=resume.file_type)
        response["Content-Disposition"] = f'attachment; filename="{resume.original_filename}"'
        response["X-Content-Type-Options"] = "nosniff"
        return response
