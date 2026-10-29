from django.urls import path

from apps.candidates.views import (
    CandidateDetailView,
    CandidateListView,
    CurrentCandidateProfileView,
)

urlpatterns = [
    path("profile/", CurrentCandidateProfileView.as_view(), name="candidate-profile"),
    path("", CandidateListView.as_view(), name="candidate-list"),
    path("<uuid:id>/", CandidateDetailView.as_view(), name="candidate-detail"),
]
