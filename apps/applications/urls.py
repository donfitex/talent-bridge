from rest_framework.routers import DefaultRouter
from apps.applications.candidate_views import CandidateApplicationViewSet

router = DefaultRouter()
router.register(r"", CandidateApplicationViewSet, basename="candidate-applications")

urlpatterns = router.urls
