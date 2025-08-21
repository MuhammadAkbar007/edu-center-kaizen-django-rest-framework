from rest_framework import viewsets
from .models import Group, RoleType, Student, Teacher
from .permissions import IsAdmin, IsAdminOrReadOnly, IsAdminOrTeacherCanWrite
from .serializers import StudentSerializer, TeacherSerializer, GroupSerializer


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrTeacherCanWrite]

    def perform_destroy(self, instance):
        user = instance.user
        user.delete()

    def get_queryset(self):
        user = self.request.user

        qs = Student.objects.select_related(
            "user", "group", "group__teacher", "group__teacher__user"
        )

        if not user.is_authenticated:
            return qs.none()
        if user.role == RoleType.ADMIN:  # pyright: ignore[reportAttributeAccessIssue]
            return qs
        if user.role == RoleType.TEACHER:  # pyright: ignore[reportAttributeAccessIssue]
            return qs.filter(group__teacher__user=user)
        if user.role == RoleType.STUDENT:  # pyright: ignore[reportAttributeAccessIssue]
            return qs.filter(user=user)
        return qs.none()


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAdmin]

    def perform_destroy(self, instance):
        user = instance.user
        user.delete()


class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Group.objects.select_related("teacher", "teacher__user")
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.role == RoleType.ADMIN:  # pyright: ignore[reportAttributeAccessIssue]
            return queryset

        if user.role == RoleType.TEACHER:  # pyright: ignore[reportAttributeAccessIssue]
            return queryset.filter(teacher__user=user)

        if user.role == RoleType.STUDENT:  # pyright: ignore[reportAttributeAccessIssue]
            try:
                student = Student.objects.only("group_id").get(user=user)
            except Student.DoesNotExist:
                return queryset.none()
            return queryset.filter(pk=student.group.id)

        return queryset.none()
