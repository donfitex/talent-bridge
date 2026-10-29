from django.urls import path

from apps.users.views import (
    CandidateRegistrationView,
    CurrentUserProfileView,
    DeactivateAccountView,
    EmailVerificationView,
    EmployerRegistrationView,
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
)

urlpatterns = [
    path("register/candidate/", CandidateRegistrationView.as_view(), name="register-candidate"),
    path("register/employer/", EmployerRegistrationView.as_view(), name="register-employer"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", CurrentUserProfileView.as_view(), name="auth-me"),
    path("password/change/", PasswordChangeView.as_view(), name="auth-password-change"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path("verify-email/", EmailVerificationView.as_view(), name="auth-verify-email"),
    path("deactivate/", DeactivateAccountView.as_view(), name="auth-deactivate"),
]
