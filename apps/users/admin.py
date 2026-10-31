from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import EmployerAccount, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "role", "is_active", "is_staff", "employer_approved"]
    search_fields = ["email", "first_name", "last_name"]
    list_filter = ["role", "is_active", "is_staff", "employer_approved"]
    fieldsets = [
        (None, {"fields": ("email", "password")}),
        (
            "Profile",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "role",
                    "is_email_verified",
                    "employer_approved",
                )
            },
        ),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
    ]
    add_fieldsets = [
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "role")})
    ]


@admin.register(EmployerAccount)
class EmployerAccountAdmin(UserAdmin):
    actions = [
        "approve_employers",
        "revoke_approval",
        "deactivate_employers",
        "reactivate_employers",
    ]
    list_display = [
        "email",
        "first_name",
        "last_name",
        "role",
        "employer_approved",
        "is_active",
        "date_joined",
    ]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(role__in=["EMPLOYER", "RECRUITER"], is_staff=False, is_superuser=False)
        )

    def has_add_permission(self, request):
        return False

    @admin.action(description="Approve selected active employer accounts", permissions=["change"])
    def approve_employers(self, request, queryset):
        count = queryset.filter(is_active=True).update(employer_approved=True)
        self.message_user(request, f"{count} active employer account(s) approved to post jobs.")

    @admin.action(description="Revoke employer posting approval", permissions=["change"])
    def revoke_approval(self, request, queryset):
        count = queryset.update(employer_approved=False)
        self.message_user(request, f"Posting approval revoked for {count} account(s).")

    @admin.action(description="Deactivate selected employer accounts", permissions=["change"])
    def deactivate_employers(self, request, queryset):
        count = queryset.update(is_active=False, employer_approved=False)
        self.message_user(
            request, f"{count} employer account(s) deactivated. Login and job posting are disabled."
        )

    @admin.action(
        description="Reactivate selected accounts (approval still required)", permissions=["change"]
    )
    def reactivate_employers(self, request, queryset):
        count = queryset.update(is_active=True, employer_approved=False)
        self.message_user(
            request, f"{count} employer account(s) reactivated and awaiting posting approval."
        )
