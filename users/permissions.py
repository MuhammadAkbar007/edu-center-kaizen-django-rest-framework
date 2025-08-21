from rest_framework.permissions import BasePermission, SAFE_METHODS

from users.models import Group, RoleType, Student


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


class IsAdminOrTeacherCanWrite(BasePermission):
    """
    - SAFE methods (GET/HEAD/OPTIONS): any authenticated user
    - Write methods (POST/PUT/PATCH/DELETE): only ADMIN or TEACHER
    - For detail writes: teacher must own the object (group/student)
    """

    def has_permission(self, request, _):  # 3rd was view
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return getattr(request.user, "role", None) in {RoleType.ADMIN, RoleType.TEACHER}

    def has_object_permission(self, request, _, obj):  # 3rd was view
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        # ADMIN can do everything
        if getattr(request.user, "role", None) == RoleType.ADMIN:
            return True

        # TEACHER: allow only for objects that belong to the teacher
        if getattr(request.user, "role", None) == RoleType.TEACHER:
            if isinstance(obj, Group):
                return obj.teacher.user.id == request.user.id
            if isinstance(obj, Student):
                return obj.group.teacher.user.id == request.user.id
        return False
