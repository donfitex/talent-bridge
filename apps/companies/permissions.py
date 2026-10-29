from rest_framework import permissions

from apps.companies.models import EmployerMembership, EmployerRole


class IsCompanyMember(permissions.BasePermission):
    """
    Allows access only to active members belonging to the specified company.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff or getattr(request.user, "is_admin_user", False):
            return True

        company = getattr(obj, "company", obj)
        return EmployerMembership.objects.filter(
            user=request.user,
            company=company,
            is_active=True,
        ).exists()


class IsCompanyAdminOrOwner(permissions.BasePermission):
    """
    Allows access only to company Owners, Admins, or platform Superadmins.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff or getattr(request.user, "is_admin_user", False):
            return True

        company = getattr(obj, "company", obj)
        return EmployerMembership.objects.filter(
            user=request.user,
            company=company,
            role__in=[EmployerRole.OWNER, EmployerRole.ADMIN],
            is_active=True,
        ).exists()
