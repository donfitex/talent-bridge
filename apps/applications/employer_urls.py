from rest_framework.routers import DefaultRouter
from apps.applications.employer_views import EmployerApplicationViewSet
router = DefaultRouter()
router.register("", EmployerApplicationViewSet, basename="employer-applications")
urlpatterns = router.urls
