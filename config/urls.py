from django.contrib import admin
from django.urls import path, include
from apps.jobs.views import JobCategoryListView, SkillListView

from apps.reports.views import RecruitmentReportView

urlpatterns = [
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/interviews/", include("apps.interviews.urls")),
    path("api/v1/employer/reports/", RecruitmentReportView.as_view()),
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/companies/", include("apps.companies.urls")),
    path("api/v1/candidates/", include("apps.candidates.urls")),
    path("api/v1/resumes/", include("apps.resumes.urls")),
    path("api/v1/applications/", include("apps.applications.urls")),
    path("api/v1/job-categories/", JobCategoryListView.as_view(), name="api-job-categories"),
    path("api/v1/skills/", SkillListView.as_view(), name="api-skills"),
    path("api/v1/employer/applications/", include("apps.applications.employer_urls")),
    path("api/v1/employer/jobs/", include("apps.jobs.employer_urls")),
    path("api/v1/jobs/", include("apps.jobs.urls")),
]
