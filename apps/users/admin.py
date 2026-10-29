from django.contrib import admin
from apps.users.models import User

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "role", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]
    list_filter = ["role", "is_active", "is_staff"]
    fieldsets = [(None, {"fields": ("email", "password")}), ("Profile", {"fields": ("first_name", "last_name", "role", "is_email_verified")}), ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")})]
    add_fieldsets = [(None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "role")})]
