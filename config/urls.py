from django.contrib import admin
from django.urls import path, include
from apps.jobs.views import JobCategoryListView, SkillListView

urlpatterns = [
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/companies/", include("apps.companies.urls")),
    path("api/v1/candidates/", include("apps.candidates.urls")),
    path("api/v1/job-categories/", JobCategoryListView.as_view(), name="api-job-categories"),
    path("api/v1/skills/", SkillListView.as_view(), name="api-skills"),
    path("api/v1/jobs/", include("apps.jobs.urls")),
]
