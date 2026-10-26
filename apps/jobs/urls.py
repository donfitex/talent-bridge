from rest_framework.routers import DefaultRouter
from apps.jobs.views import PublicJobViewSet

router = DefaultRouter()
router.register(r"", PublicJobViewSet, basename="public-jobs")

urlpatterns = router.urls
