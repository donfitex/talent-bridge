from rest_framework import serializers
from apps.candidates.models import CandidateProfile


class CandidateProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    completeness_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = CandidateProfile
        fields = [
            "id",
            "email",
            "full_name",
            "professional_title",
            "biography",
            "location",
            "country",
            "phone",
            "years_of_experience",
            "employment_type_preference",
            "remote_work_preference",
            "is_public",
            "is_contact_visible",
            "completeness_score",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "completeness_score", "created_at", "updated_at"]


class PublicCandidateProfileSerializer(serializers.ModelSerializer):
    """Sanitized view of a candidate profile protecting private contact details."""
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    completeness_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = CandidateProfile
        fields = [
            "id",
            "full_name",
            "professional_title",
            "biography",
            "location",
            "country",
            "years_of_experience",
            "employment_type_preference",
            "remote_work_preference",
            "completeness_score",
        ]
        read_only_fields = fields
