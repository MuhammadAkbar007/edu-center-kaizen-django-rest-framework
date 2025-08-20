from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import uuid


class CustomUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required")

        extra_fields.setdefault("role", "STUDENT")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class RoleType(models.TextChoices):  # just role enum
    ADMIN = "ADMIN", "Admin"
    TEACHER = "TEACHER", "Teacher"
    STUDENT = "STUDENT", "Student"


class StudentStatus(models.TextChoices):
    EXPELLED = "EXPELLED", "Expelled"
    GRADUATED = "GRADUATED", "Graduated"
    STUDYING = "STUDYING", "Studying"


class GroupStatus(models.TextChoices):
    STUDYING = "STUDYING", "Studying"
    COMPLETED = "COMPLETED", "Completed"
    TERMINATED = "TERMINATED", "Terminated"


class User(AbstractUser):
    # INFO: AbstractUser already has: username, password, first_name, last_name, email etc

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # INFO: not to use in auth & not to create column in db table
    first_name = models.CharField(max_length=50, null=False, blank=False)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=32, unique=True, null=False, blank=False)
    email = models.EmailField(unique=True, null=False, blank=False)
    role = models.CharField(
        max_length=20, choices=RoleType.choices, default=RoleType.STUDENT
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"  # INFO: now email is used to log in
    REQUIRED_FIELDS = ["role", "phone_number", "first_name"]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    date_of_birth = models.DateField()
    enrollment_date = models.DateField(default=timezone.now)
    status = models.CharField(
        max_length=20,
        choices=StudentStatus.choices,
        default=StudentStatus.STUDYING,
    )
    group = models.ForeignKey(
        "Group", on_delete=models.PROTECT, related_name="students"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.user.role != RoleType.STUDENT:
            raise ValidationError("Linked user must have role=STUDENT")

        if Teacher.objects.filter(user=self.user).exists():
            raise ValidationError("A user cannot be both a Teacher and a Student")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.status})"


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    qualification = models.CharField(max_length=100, blank=True, null=True)
    hired_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.user.role != RoleType.TEACHER:
            raise ValidationError("Linked user must have role=TEACHER")

        if Student.objects.filter(user=self.user).exists():
            raise ValidationError("A user cannot be both a Teacher and a Student")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.specialization})"


class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, blank=False, null=False)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=100, null=False, blank=False)
    status = models.CharField(
        max_length=20, choices=GroupStatus.choices, default=GroupStatus.STUDYING
    )
    teacher = models.ForeignKey(
        Teacher, on_delete=models.PROTECT, related_name="groups"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
