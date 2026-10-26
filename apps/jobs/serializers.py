from rest_framework import serializers
from apps.jobs.models import JobCategory, Skill


class JobCategorySerializer(serializers.ModelSerializer):
    skills_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = JobCategory
        fields = ["id", "name", "slug", "description", "icon", "is_active", "skills_count", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]

    def get_skills_count(self, obj) -> int:
        return obj.skills.count()


class SkillSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Skill
        fields = ["id", "name", "slug", "category", "category_name", "is_verified", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]

    def validate_name(self, value):
        cleaned = value.strip()
        if Skill.objects.filter(name__iexact=cleaned).exists():
            raise serializers.ValidationError(f"A skill named '{cleaned}' already exists.")
        return cleaned
