from rest_framework import permissions


class IsCandidateUser(permissions.BasePermission):
    """Allows access only to candidate users."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_candidate", False)
        )


class IsEmployerUser(permissions.BasePermission):
    """Allows access only to employer / recruiter users."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, "is_employer", False)
                or getattr(request.user, "is_recruiter", False)
                or getattr(request.user, "is_admin_user", False)
            )
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """Allows access only to the object owner or staff/admin."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or getattr(request.user, "is_admin_user", False):
            return True
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "candidate") and hasattr(obj.candidate, "user"):
            return obj.candidate.user == request.user
        return False


def can_create_company(user):
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and (
            user.is_staff
            or user.is_admin_user
            or ((user.is_employer or user.is_recruiter) and user.employer_approved)
        )
    )


class IsApprovedCompanyCreator(permissions.BasePermission):
    message = (
        "Your employer account must be approved by an administrator before you can add a company."
    )

    def has_permission(self, request, view):
        return can_create_company(request.user)
