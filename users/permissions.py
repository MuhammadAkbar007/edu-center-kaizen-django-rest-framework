from rest_framework.permissions import BasePermission, SAFE_METHODS

from users.models import RoleType


class IsAdmin(BasePermission):
    """
    Allows access only to users with role = ADMIN
    """

    def has_permission(self, request, _):  # 3rd was view
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == RoleType.ADMIN
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Admins can do everything.
    Other authenticated users can only read (GET, HEAD, OPTIONS).
    """

    def has_permission(self, request, _):  # 3rd was view
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role == RoleType.ADMIN
