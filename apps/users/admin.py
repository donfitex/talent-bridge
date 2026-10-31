from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User


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
