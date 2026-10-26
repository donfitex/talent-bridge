from rest_framework.routers import DefaultRouter
from apps.jobs.employer_views import EmployerJobViewSet

router = DefaultRouter()
router.register(r"", EmployerJobViewSet, basename="employer-jobs")

urlpatterns = router.urls
