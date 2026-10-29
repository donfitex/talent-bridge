from rest_framework import viewsets, permissions, status, decorators
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.common.responses import APIResponse
from apps.common.permissions import IsEmployerUser
from django.db import transaction
from apps.common.exceptions import TalentBridgeAPIException
from apps.users.models import User, UserRole
from apps.companies.models import Company, EmployerMembership, EmployerRole
from apps.companies.serializers import (
    CompanySerializer,
    EmployerMembershipSerializer,
    AssignRecruiterSerializer,
)
from apps.companies.permissions import IsCompanyMember, IsCompanyAdminOrOwner


class CompanyViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Company Profiles and Employer Memberships.
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    lookup_field = "id"

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        if self.action == "create":
            return [IsEmployerUser()]
        if self.action == "members":
            return [permissions.IsAuthenticated(), IsCompanyMember()]
        return [permissions.IsAuthenticated(), IsCompanyAdminOrOwner()]

    @transaction.atomic
    def perform_create(self, serializer):
        company = serializer.save()
        # Automatically make creator the OWNER of this company
        EmployerMembership.objects.create(
            user=self.request.user,
            company=company,
            role=EmployerRole.OWNER,
            is_active=True,
        )
        # Update user's primary role to EMPLOYER if currently CANDIDATE
        if self.request.user.role == UserRole.CANDIDATE:
            self.request.user.role = UserRole.EMPLOYER
            self.request.user.save(update_fields=["role"])

    @extend_schema(
        responses={200: EmployerMembershipSerializer(many=True)},
        description="Retrieve active members and recruiters of this company.",
    )
    @decorators.action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated, IsCompanyMember],
    )
    def members(self, request, id=None):
        company = self.get_object()
        memberships = company.memberships.filter(is_active=True).select_related("user")
        serializer = EmployerMembershipSerializer(memberships, many=True)
        return APIResponse(data=serializer.data)

    @extend_schema(
        request=AssignRecruiterSerializer,
        responses={201: EmployerMembershipSerializer},
        description="Assign a recruiter to the company organization.",
    )
    @members.mapping.post
    def add_member(self, request, id=None):
        company = self.get_object()
        serializer = AssignRecruiterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]

        try:
            target_user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise TalentBridgeAPIException(
                detail=f"User with email '{email}' does not exist. They must register first.",
                code="USER_NOT_FOUND",
            )

        membership, created = EmployerMembership.objects.get_or_create(
            user=target_user,
            company=company,
            defaults={"role": role, "is_active": True},
        )
        if not created:
            if membership.role == EmployerRole.OWNER:
                raise TalentBridgeAPIException(detail="Owner membership cannot be reassigned.", status_code=409)
            if not membership.is_active:
                membership.is_active = True
                membership.role = role
                membership.save(update_fields=["is_active", "role"])
            else:
                membership.role = role
                membership.save(update_fields=["role"])

        # Ensure user role is at least RECRUITER
        if target_user.role == UserRole.CANDIDATE:
            target_user.role = UserRole.RECRUITER
            target_user.save(update_fields=["role"])

        return APIResponse(
            data=EmployerMembershipSerializer(membership).data,
            status_code=status.HTTP_201_CREATED,
            message=f"Recruiter {email} successfully assigned to {company.name}.",
        )

    @decorators.action(
        detail=True,
        methods=["delete"],
        url_path="members/(?P<member_id>[^/.]+)",
        permission_classes=[permissions.IsAuthenticated, IsCompanyAdminOrOwner],
    )
    def remove_member(self, request, id=None, member_id=None):
        company = self.get_object()
        membership = get_object_or_404(EmployerMembership, id=member_id, company=company)

        if membership.role == EmployerRole.OWNER:
            raise TalentBridgeAPIException(
                detail="Company owners cannot remove themselves from their own company.",
                code="CANNOT_REMOVE_OWNER",
            )

        membership.is_active = False
        membership.save(update_fields=["is_active"])
        return APIResponse(data={}, message="Recruiter access revoked successfully.")
