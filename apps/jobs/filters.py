import django_filters
from django.db.models import Q
from django.utils import timezone
from apps.jobs.models import Job, EmploymentType, WorkplaceType, ExperienceLevel


class JobFilter(django_filters.FilterSet):
    """
    Comprehensive query filter for public job discovery.
    Supports keywords, title, company, category, skills, location, salary, and dates.
    """
    q = django_filters.CharFilter(method="filter_keywords", label="Keyword Search")
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    company = django_filters.CharFilter(field_name="company__name", lookup_expr="icontains")
    company_slug = django_filters.CharFilter(field_name="company__slug", lookup_expr="exact")
    category = django_filters.CharFilter(field_name="category__slug", lookup_expr="exact")
    skills = django_filters.CharFilter(method="filter_skills", label="Filter by Skill Slug or Name")
    country = django_filters.CharFilter(field_name="country", lookup_expr="iexact")
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    employment_type = django_filters.ChoiceFilter(choices=EmploymentType.choices)
    workplace_type = django_filters.ChoiceFilter(choices=WorkplaceType.choices)
    experience_level = django_filters.ChoiceFilter(choices=ExperienceLevel.choices)
    salary_min = django_filters.NumberFilter(field_name="salary_min", lookup_expr="gte")
    salary_max = django_filters.NumberFilter(field_name="salary_max", lookup_expr="lte")
    published_after = django_filters.IsoDateTimeFilter(field_name="published_at", lookup_expr="gte")
    deadline_after = django_filters.IsoDateTimeFilter(field_name="application_deadline", lookup_expr="gte")

    class Meta:
        model = Job
        fields = [
            "q",
            "title",
            "company",
            "company_slug",
            "category",
            "skills",
            "country",
            "location",
            "employment_type",
            "workplace_type",
            "experience_level",
            "salary_min",
            "salary_max",
            "published_after",
            "deadline_after",
        ]

    def filter_keywords(self, queryset, name, value):
        if not value:
            return queryset
        val = value.strip()
        return queryset.filter(
            Q(title__icontains=val)
            | Q(description__icontains=val)
            | Q(requirements__icontains=val)
            | Q(responsibilities__icontains=val)
            | Q(company__name__icontains=val)
            | Q(job_skills__skill__name__icontains=val)
        ).distinct()

    def filter_skills(self, queryset, name, value):
        if not value:
            return queryset
        skills_list = [s.strip() for s in value.split(",") if s.strip()]
        return queryset.filter(
            Q(job_skills__skill__name__in=skills_list)
            | Q(job_skills__skill__slug__in=skills_list)
        ).distinct()
