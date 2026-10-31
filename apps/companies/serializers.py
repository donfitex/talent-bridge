from rest_framework import serializers

from apps.companies.models import Company, EmployerMembership, EmployerRole


class CompanySerializer(serializers.ModelSerializer):
    display_logo_url = serializers.CharField(read_only=True)
    members_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "industry",
            "company_size",
            "website",
            "logo",
            "display_logo_url",
            "location",
            "country",
            "verification_status",
            "members_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "verification_status", "created_at", "updated_at"]

    def get_members_count(self, obj) -> int:
        return obj.memberships.filter(is_active=True).count()


class EmployerMembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = EmployerMembership
        fields = [
            "id",
            "user",
            "user_email",
            "user_name",
            "company",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AssignRecruiterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(
        choices=[EmployerRole.ADMIN, EmployerRole.RECRUITER],
        default=EmployerRole.RECRUITER,
    )

    def validate_email(self, value):
        return value.lower()
