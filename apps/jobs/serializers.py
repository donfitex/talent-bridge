from rest_framework import serializers
from django.db import transaction
from apps.jobs.models import JobCategory, Skill, Job, JobSkill, JobStatus


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


class JobSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source="skill.name", read_only=True)

    class Meta:
        model = JobSkill
        fields = ["id", "skill", "skill_name", "is_required"]
        read_only_fields = ["id"]


class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    company_logo = serializers.ImageField(source="company.logo", read_only=True)
    company_slug = serializers.CharField(source="company.slug", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    is_accepting_applications = serializers.BooleanField(read_only=True)
    skills = JobSkillSerializer(source="job_skills", many=True, read_only=True)
    skill_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of Skill UUIDs to attach to this job",
    )

    class Meta:
        model = Job
        fields = [
            "id",
            "company",
            "company_name",
            "company_logo",
            "company_slug",
            "created_by",
            "title",
            "slug",
            "description",
            "responsibilities",
            "requirements",
            "category",
            "category_name",
            "employment_type",
            "workplace_type",
            "experience_level",
            "location",
            "country",
            "salary_min",
            "salary_max",
            "salary_currency",
            "salary_period",
            "status",
            "published_at",
            "application_deadline",
            "is_accepting_applications",
            "skills",
            "skill_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "created_by",
            "published_at",
            "is_accepting_applications",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        salary_min = attrs.get("salary_min", getattr(self.instance, "salary_min", None))
        salary_max = attrs.get("salary_max", getattr(self.instance, "salary_max", None))
        for value in [salary_min, salary_max]:
            if value is not None and value < 0:
                raise serializers.ValidationError("Salary must be nonnegative.")
        skill_ids = attrs.get("skill_ids", [])
        if len(set(skill_ids)) != len(skill_ids) or Skill.objects.filter(pk__in=skill_ids).count() != len(skill_ids):
            raise serializers.ValidationError({"skill_ids": "Supply unique existing skill IDs."})
        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise serializers.ValidationError({
                "salary_min": "Minimum salary cannot exceed maximum salary."
            })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        skill_ids = validated_data.pop("skill_ids", [])
        job = Job.objects.create(**validated_data)
        for skill_id in skill_ids:
            try:
                skill = Skill.objects.get(id=skill_id)
                JobSkill.objects.create(job=job, skill=skill, is_required=True)
            except Skill.DoesNotExist:
                pass
        return job

    @transaction.atomic
    def update(self, instance, validated_data):
        skill_ids = validated_data.pop("skill_ids", None)
        job = super().update(instance, validated_data)
        if skill_ids is not None:
            job.job_skills.all().delete()
            for skill_id in skill_ids:
                try:
                    skill = Skill.objects.get(id=skill_id)
                    JobSkill.objects.create(job=job, skill=skill, is_required=True)
                except Skill.DoesNotExist:
                    pass
        return job
