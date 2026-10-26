from django.urls import path
from apps.candidates.views import (
    CurrentCandidateProfileView,
    CandidateDetailView,
    CandidateListView,
)

urlpatterns = [
    path("profile/", CurrentCandidateProfileView.as_view(), name="candidate-profile"),
    path("", CandidateListView.as_view(), name="candidate-list"),
    path("<uuid:id>/", CandidateDetailView.as_view(), name="candidate-detail"),
]
