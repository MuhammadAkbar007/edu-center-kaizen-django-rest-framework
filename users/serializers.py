from rest_framework import serializers
from .models import Group, Student, Teacher


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "description",
            "subject",
            "status",
            "created_at",
            "updated_at",
        ]


class StudentSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), source="group", write_only=True
    )

    class Meta:
        model = Student
        fields = [
            "id",
            "user",
            "date_of_birth",
            "enrollment_date",
            "status",
            "created_at",
            "updated_at",
            "group",
            "group_id",
        ]

    def validate(self, attrs):
        user = attrs["user"]

        if user.role != "STUDENT":
            raise serializers.ValidationError("Linked user must have role=STUDENT")

        if Teacher.objects.filter(user=user).exists():
            raise serializers.ValidationError(
                "A user cannot be both a Teacher and a Student"
            )

        return attrs


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = [
            "id",
            "user",
            "specialization",
            "qualification",
            "hired_date",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        user = attrs["user"]

        if user.role != "TEACHER":
            raise serializers.ValidationError("Linked user must have role=TEACHER")

        if Student.objects.filter(user=user).exists():
            raise serializers.ValidationError(
                "A user cannot be both a Teacher and a Student"
            )

        return attrs
