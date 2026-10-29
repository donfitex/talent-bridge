from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, viewsets

from apps.common.responses import APIResponse
from apps.jobs.filters import JobFilter
from apps.jobs.models import Job, JobCategory, JobStatus, Skill
from apps.jobs.serializers import JobCategorySerializer, JobSerializer, SkillSerializer


class JobCategoryListView(generics.ListCreateAPIView):
    """
    GET /api/v1/job-categories/
    List active job categories.
    """

    queryset = JobCategory.objects.filter(is_active=True).prefetch_related("skills")
    serializer_class = JobCategorySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return APIResponse(data=response.data)


class SkillListView(generics.ListCreateAPIView):
    """
    GET /api/v1/skills/
    Search and list skills taxonomy.
    """

    serializer_class = SkillSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        qs = Skill.objects.all().select_related("category")
        q = self.request.query_params.get("q")
        category = self.request.query_params.get("category")
        if q:
            qs = qs.filter(name__icontains=q)
        if category:
            qs = qs.filter(category__slug=category)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return APIResponse(data=response.data)


class PublicJobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API for discovering and inspecting published job vacancies.
    GET /api/v1/jobs/
    GET /api/v1/jobs/{id}/
    """

    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = JobFilter
    ordering_fields = ["published_at", "salary_max", "salary_min", "title"]
    ordering = ["-published_at"]

    def get_queryset(self):
        """Only returns eligible, published vacancies whose deadline has not expired."""
        now = timezone.now()
        return (
            Job.objects.filter(status=JobStatus.PUBLISHED)
            .filter(Q(application_deadline__isnull=True) | Q(application_deadline__gt=now))
            .select_related("company", "category")
            .prefetch_related("job_skills__skill")
        )
