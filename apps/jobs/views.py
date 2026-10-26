from rest_framework import generics, permissions, status
from apps.common.responses import APIResponse
from apps.jobs.models import JobCategory, Skill
from apps.jobs.serializers import JobCategorySerializer, SkillSerializer


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
