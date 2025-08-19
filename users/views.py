from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdmin
from .models import Group, Student, Teacher
from .serializers import StudentSerializer, TeacherSerializer, GroupSerializer


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAdmin]


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdmin]
