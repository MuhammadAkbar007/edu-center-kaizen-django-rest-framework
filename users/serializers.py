from typing import cast

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import CustomUserManager, Group, Student, Teacher


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
    # User-specific fields
    id = serializers.UUIDField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email")
    password = serializers.CharField(source="user.password", write_only=True)
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    phone_number = serializers.CharField(source="user.phone_number")
    role = serializers.CharField(source="user.role", read_only=True)

    # Teacher-specific fields
    specialization = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    qualification = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    hired_date = serializers.DateField(required=False, default=timezone.now)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "password",
            "specialization",
            "qualification",
            "hired_date",
            "role",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        password = user_data.pop("password")

        User = get_user_model()
        manager = cast(CustomUserManager, User.objects)
        user = manager.create_user(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            phone_number=user_data["phone_number"],
            email=user_data["email"],
            password=password,
            role="TEACHER",
            is_staff=True,
        )

        return Teacher.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        user_data = validated_data.get("user", {})
        password = user_data.pop("password", None)

        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)

        if password:
            user.set_password(password)
        user.save()

        for attr, value in validated_data.items():
            if attr != "user":
                setattr(instance, attr, value)
        instance.save()

        return instance

    def validate(self, attrs):
        User = get_user_model()
        user_data = attrs.get("user", {})
        email = user_data.get("email")

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists")

        if User.objects.filter(email=email, role="STUDENT").exists():
            raise serializers.ValidationError(
                "A user cannot be both a Teacher and a Student"
            )

        return attrs
