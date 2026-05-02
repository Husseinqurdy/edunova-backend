from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone as tz
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email is required'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', _('Super Admin')
        TENANT_ADMIN = 'tenant_admin', _('Tenant Admin')
        INSTRUCTOR = 'instructor', _('Instructor')
        STUDENT = 'student', _('Student')
        STAFF = 'staff', _('Staff')

    class Language(models.TextChoices):
        EN = 'en', 'English'
        SW = 'sw', 'Kiswahili'
        FR = 'fr', 'Français'
        AR = 'ar', 'العربية'
        ES = 'es', 'Español'
        PT = 'pt', 'Português'
        ZH = 'zh', '中文'
        HI = 'hi', 'हिन्दी'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    preferred_language = models.CharField(max_length=5, choices=Language.choices, default=Language.EN)
    user_timezone = models.CharField(max_length=50, default='UTC')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=tz.now)
    last_login = models.DateTimeField(null=True, blank=True)
    notification_preferences = models.JSONField(default=dict)
    social_links = models.JSONField(default=dict)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_tenant_admin(self):
        return self.role == self.Role.TENANT_ADMIN


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    headline = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    expertise = models.JSONField(default=list)
    total_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    badges = models.JSONField(default=list)
    streak_days = models.IntegerField(default=0)
    last_activity = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Profile: {self.user.email}"
