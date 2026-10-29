from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, views

from apps.candidates.models import CandidateProfile
from apps.candidates.serializers import (
    CandidateProfileSerializer,
    PublicCandidateProfileSerializer,
)
from apps.common.permissions import IsCandidateUser
from apps.common.responses import APIResponse


class CurrentCandidateProfileView(views.APIView):
    """
    Candidate endpoint to retrieve and update own candidate profile.
    Automatically initializes profile if it does not exist yet.
    """

    permission_classes = [IsCandidateUser]

    @extend_schema(responses={200: CandidateProfileSerializer})
    def get(self, request):
        profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        serializer = CandidateProfileSerializer(profile)
        return APIResponse(data=serializer.data)

    @extend_schema(request=CandidateProfileSerializer, responses={200: CandidateProfileSerializer})
    def patch(self, request):
        profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        serializer = CandidateProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse(data=serializer.data, message="Candidate profile updated successfully.")


class CandidateDetailView(views.APIView):
    """
    Endpoint for viewing candidate details.
    Enforces privacy rules: hides phone and private data unless authorized.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CandidateProfileSerializer})
    def get(self, request, id):
        profile = get_object_or_404(CandidateProfile.objects.select_related("user"), id=id)

        # Full profile if current user is the candidate or staff
        if profile.user == request.user or request.user.is_staff:
            serializer = CandidateProfileSerializer(profile)
            return APIResponse(data=serializer.data)

        if not profile.is_public:
            from django.http import Http404

            raise Http404
        # Otherwise check if contact info is allowed or public view
        if (
            profile.is_contact_visible
            and (request.user.is_employer or request.user.is_recruiter)
            and request.user.employer_memberships.filter(
                is_active=True, company__verification_status="VERIFIED"
            ).exists()
        ):
            serializer = CandidateProfileSerializer(profile)
        else:
            serializer = PublicCandidateProfileSerializer(profile)

        return APIResponse(data=serializer.data)


class CandidateListView(generics.ListAPIView):
    """
    Endpoint for searching and listing public candidates.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PublicCandidateProfileSerializer

    def get_queryset(self):
        qs = CandidateProfile.objects.filter(is_public=True, user__is_active=True).select_related(
            "user"
        )
        title = self.request.query_params.get("title")
        country = self.request.query_params.get("country")
        if title:
            qs = qs.filter(professional_title__icontains=title)
        if country:
            qs = qs.filter(country__iexact=country)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return APIResponse(data=response.data)
