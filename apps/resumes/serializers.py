from rest_framework import serializers

from apps.resumes.models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Resume
        fields = [
            "id",
            "title",
            "original_filename",
            "file_type",
            "file_size",
            "is_default",
            "download_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_default",
            "original_filename",
            "file_type",
            "file_size",
            "download_url",
            "created_at",
            "updated_at",
        ]

    def get_download_url(self, obj) -> str:
        request = self.context.get("request")
        url = f"/api/v1/resumes/{obj.id}/download/"
        return request.build_absolute_uri(url) if request else url


class ResumeUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    file = serializers.FileField(required=True)
    is_default = serializers.BooleanField(default=False)
