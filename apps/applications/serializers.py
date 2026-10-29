from rest_framework import serializers
from apps.applications.models import JobApplication, ApplicationStatus
from apps.jobs.serializers import JobSerializer
from apps.resumes.serializers import ResumeSerializer


class ApplicationSubmissionSerializer(serializers.Serializer):
    resume_id = serializers.UUIDField(required=True)
    cover_letter = serializers.CharField(required=False, allow_blank=True, default="")


class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)
    company_slug = serializers.CharField(source="job.company.slug", read_only=True)
    resume_title = serializers.CharField(source="resume.title", read_only=True)
    resume_url = serializers.SerializerMethodField()

    class Meta:
        model = JobApplication
        fields = [
            "id",
            "job",
            "job_title",
            "company_name",
            "company_slug",
            "resume",
            "resume_title",
            "resume_url",
            "cover_letter",
            "status",
            "applied_at",
            "updated_at",
            "withdrawn_at",
        ]
        read_only_fields = [
            "id",
            "job",
            "job_title",
            "company_name",
            "company_slug",
            "status",
            "applied_at",
            "updated_at",
            "withdrawn_at",
        ]

    def get_resume_url(self, obj) -> str:
        return f"/api/v1/resumes/{obj.resume_id}/download/"
