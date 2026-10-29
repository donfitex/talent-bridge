from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.applications.views import JobApplicationSubmissionView
from apps.jobs.views import PublicJobViewSet

router = DefaultRouter()
router.register(r"", PublicJobViewSet, basename="public-jobs")

urlpatterns = [
    path("<uuid:id>/apply/", JobApplicationSubmissionView.as_view(), name="job-apply"),
] + router.urls
