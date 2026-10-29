from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status, views

from apps.common.exceptions import TalentBridgeAPIException
from apps.common.responses import APIResponse
from apps.users.models import UserRole
from apps.users.serializers import (
    EmailVerificationSerializer,
    EmptyRequestSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)
from apps.users.services import UserService


class CandidateRegistrationView(views.APIView):
    """Public endpoint for registering a candidate user account."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=UserRegistrationSerializer,
        responses={201: UserProfileSerializer},
        description="Register a new Candidate user account.",
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(
            data=request.data, context={"role": UserRole.CANDIDATE}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return APIResponse(
            data=UserProfileSerializer(user).data,
            status_code=status.HTTP_201_CREATED,
            message="Candidate registration successful. Please check your email to verify your account.",
        )


class EmployerRegistrationView(views.APIView):
    """Public endpoint for registering an employer user account."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=UserRegistrationSerializer,
        responses={201: UserProfileSerializer},
        description="Register a new Employer user account.",
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(
            data=request.data, context={"role": UserRole.EMPLOYER}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return APIResponse(
            data=UserProfileSerializer(user).data,
            status_code=status.HTTP_201_CREATED,
            message="Employer registration successful. Please verify your email.",
        )


@method_decorator(csrf_protect, name="dispatch")
class LoginView(views.APIView):
    """Authenticates credentials and establishes session."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=UserLoginSerializer,
        responses={200: UserProfileSerializer},
        description="Log in with email and password.",
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return APIResponse(
            data=UserProfileSerializer(user).data,
            message="Login successful.",
        )


class LogoutView(views.APIView):
    serializer_class = EmptyRequestSerializer
    """Terminates authenticated session."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: OpenApiResponse(description="Logged out successfully")})
    def post(self, request):
        logout(request)
        return APIResponse(data={}, message="Logged out successfully.")


class CurrentUserProfileView(views.APIView):
    """Returns or updates current authenticated user profile."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: UserProfileSerializer})
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return APIResponse(data=serializer.data)

    @extend_schema(request=UserProfileSerializer, responses={200: UserProfileSerializer})
    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse(data=serializer.data, message="Profile updated successfully.")


class PasswordChangeView(views.APIView):
    """Allows authenticated user to change password."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=PasswordChangeSerializer, responses={200: OpenApiResponse()})
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse(data={}, message="Password changed successfully.")


class PasswordResetRequestView(views.APIView):
    """Dispatches password reset email token."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: OpenApiResponse()})
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        UserService.request_password_reset(serializer.validated_data["email"])
        return APIResponse(
            data={},
            message="If an active account exists with this email address, password reset instructions have been sent.",
        )


class PasswordResetConfirmView(views.APIView):
    """Sets new password using reset token."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=PasswordResetConfirmSerializer, responses={200: OpenApiResponse()})
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        success = UserService.confirm_password_reset(
            uidb64=serializer.validated_data["uid"],
            token=serializer.validated_data["token"],
            new_password=serializer.validated_data["new_password"],
        )
        if not success:
            raise TalentBridgeAPIException(
                detail="The password reset link is invalid or has expired.",
                code="INVALID_RESET_TOKEN",
            )
        return APIResponse(
            data={}, message="Password has been reset successfully. You may now log in."
        )


class EmailVerificationView(views.APIView):
    """Verifies account email address."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=EmailVerificationSerializer, responses={200: OpenApiResponse()})
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        success = UserService.verify_email(
            uidb64=serializer.validated_data["uid"],
            token=serializer.validated_data["token"],
        )
        if not success:
            raise TalentBridgeAPIException(
                detail="The email verification link is invalid or has expired.",
                code="INVALID_VERIFICATION_TOKEN",
            )
        return APIResponse(data={}, message="Email address verified successfully.")


class DeactivateAccountView(views.APIView):
    serializer_class = EmptyRequestSerializer
    """Allows user to deactivate their account."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: OpenApiResponse()})
    def post(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        logout(request)
        return APIResponse(data={}, message="Account deactivated successfully.")
