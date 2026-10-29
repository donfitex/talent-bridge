from rest_framework.routers import DefaultRouter

from apps.resumes.views import ResumeViewSet

router = DefaultRouter()
router.register(r"", ResumeViewSet, basename="resumes")

urlpatterns = router.urls
