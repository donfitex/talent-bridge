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
