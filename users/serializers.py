from typing import cast

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import CustomUserManager, Group, Student, StudentStatus, Teacher, RoleType


class TeacherSerializer(serializers.ModelSerializer):
    # User-specific fields
    id = serializers.UUIDField(source="user.id", read_only=True)
    email = serializers.EmailField(
        source="user.email",
        validators=[
            UniqueValidator(
                queryset=get_user_model().objects.all(),
                message="Email must be unique.",
            )
        ],
    )
    password = serializers.CharField(source="user.password", write_only=True)
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    phone_number = serializers.CharField(
        source="user.phone_number",
        validators=[
            UniqueValidator(
                queryset=get_user_model().objects.all(),
                message="Phone number must be unique.",
            )
        ],
    )
    role = serializers.CharField(source="user.role", read_only=True)

    # Teacher-specific fields
    specialization = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    qualification = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    hired_date = serializers.DateField(required=False, default=timezone.localdate)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "specialization",
            "qualification",
            "hired_date",
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
            role=RoleType.TEACHER,
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

        if User.objects.filter(email=email, role=RoleType.STUDENT).exists():
            raise serializers.ValidationError(
                "A user cannot be both a Teacher and a Student"
            )

        return attrs


class GroupSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="teacher", write_only=True, required=True
    )
    name = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=Group.objects.all(), message="Group name must be unique."
            )
        ]
    )

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "description",
            "subject",
            "status",
            "teacher",  # read-only projection
            "teacher_id",  # write-only FK for create/update
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "teacher", "created_at", "updated_at"]
        extra_kwargs = {
            "description": {"required": False, "allow_null": True, "allow_blank": True}
        }

    def validate(self, attrs):
        if self.instance is None and "teacher" not in attrs:
            raise serializers.ValidationError({"teacher_id": "This field is required."})
        return attrs


class StudentSerializer(serializers.ModelSerializer):
    # User-specific fields
    id = serializers.UUIDField(source="user.id", read_only=True)
    email = serializers.EmailField(
        source="user.email",
        validators=[
            UniqueValidator(
                queryset=get_user_model().objects.all(),
                message="Email must be unique.",
            )
        ],
    )
    password = serializers.CharField(source="user.password", write_only=True)
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    phone_number = serializers.CharField(
        source="user.phone_number",
        validators=[
            UniqueValidator(
                queryset=get_user_model().objects.all(),
                message="Phone number must be unique.",
            )
        ],
    )
    role = serializers.CharField(source="user.role", read_only=True)

    # User-specific fields
    date_of_birth = serializers.DateField()
    enrollment_date = serializers.DateField(required=False, default=timezone.localdate)
    status = serializers.CharField(required=False, default=StudentStatus.STUDYING)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    group = GroupSerializer(read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), source="group", write_only=True
    )

    class Meta:
        model = Student
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "date_of_birth",
            "enrollment_date",
            "status",
            "created_at",
            "updated_at",
            "group",
            "group_id",
        ]

    def validate(self, attrs):
        """
        - Email uniqueness (create + update)
        - Teacher can only assign to their own groups (create + update when group changes)
        - No overlap with Teacher account
        """
        request = self.context.get("request")
        User = get_user_model()
        user_data = attrs.get("user", {})
        email = user_data.get("email")

        group = attrs.get("group")
        instance = getattr(self, "instance", None)

        # check Email uniqueness
        if email:
            qs = User.objects.filter(email=email)
            if instance:
                qs = qs.exclude(pk=instance.user.id)
            if qs.exists():
                raise serializers.ValidationError(
                    {"email": "This email is already in use."}
                )

        # Group ownership restriction for TEACHER
        if request and getattr(request.user, "role", None) == RoleType.TEACHER:
            # On create, `group` must be present; on update, it might or might not be provided
            target_group = group or (instance.group if instance else None)
            if target_group and target_group.teacher.user != request.user:
                raise serializers.ValidationError(
                    "You can only assign students to groups you teach."
                )

        return attrs

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
            role=RoleType.STUDENT,
        )

        return Student.objects.create(user=user, **validated_data)

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
