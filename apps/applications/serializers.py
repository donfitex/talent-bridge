from rest_framework import serializers

from apps.applications.models import ApplicationStatus, JobApplication


class ApplicationSubmissionSerializer(serializers.Serializer):
    resume_id = serializers.UUIDField(required=True)
    cover_letter = serializers.CharField(required=False, allow_blank=True, default="")


class JobApplicationSerializer(serializers.ModelSerializer):
    applied_at = serializers.DateTimeField(source="created_at", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)
    company_slug = serializers.CharField(source="job.company.slug", read_only=True)
    resume_title = serializers.CharField(source="resume.title", read_only=True)
    resume_url = serializers.SerializerMethodField()

    history = serializers.SerializerMethodField()

    def get_history(self, obj) -> list[dict]:
        return [
            {
                "previous_status": item.previous_status,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in obj.history.all()
        ]

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
            "history",
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
            "history",
        ]

    def get_resume_url(self, obj) -> str:
        return f"/api/v1/resumes/{obj.resume_id}/download/"


class StatusTransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ApplicationStatus.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=5000)


class EmployerApplicationSerializer(JobApplicationSerializer):
    candidate_name = serializers.CharField(source="candidate.user.get_full_name", read_only=True)
    candidate_email = serializers.EmailField(source="candidate.user.email", read_only=True)

    class Meta(JobApplicationSerializer.Meta):
        fields = JobApplicationSerializer.Meta.fields + ["candidate_name", "candidate_email"]
