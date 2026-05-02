from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class Tenant(models.Model):
    class TenantType(models.TextChoices):
        SCHOOL = 'school', _('School / University')
        CORPORATE = 'corporate', _('Corporate Training')
        BOOTCAMP = 'bootcamp', _('Bootcamp / Academy')
        NGO = 'ngo', _('NGO / Non-profit')
        INDIVIDUAL = 'individual', _('Individual Creator')

    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        SUSPENDED = 'suspended', _('Suspended')
        TRIAL = 'trial', _('Trial')
        PENDING = 'pending', _('Pending Setup')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    tenant_type = models.CharField(max_length=20, choices=TenantType.choices, default=TenantType.SCHOOL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)

    # Branding
    logo = models.ImageField(upload_to='tenants/logos/', blank=True, null=True)
    favicon = models.ImageField(upload_to='tenants/favicons/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#6366f1')
    secondary_color = models.CharField(max_length=7, default='#8b5cf6')
    accent_color = models.CharField(max_length=7, default='#06b6d4')
    text_color = models.CharField(max_length=7, default='#1e293b')
    background_color = models.CharField(max_length=7, default='#ffffff')
    font_family = models.CharField(max_length=100, default='DM Sans')
    custom_css = models.TextField(blank=True)

    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    default_language = models.CharField(max_length=5, default='en')
    supported_languages = models.JSONField(default=list)
    custom_domain = models.CharField(max_length=253, blank=True)

    subscription = models.ForeignKey(
        'subscriptions.Subscription', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tenant'
    )

    max_students = models.IntegerField(default=50)
    max_instructors = models.IntegerField(default=5)
    max_storage_gb = models.FloatField(default=5.0)
    used_storage_gb = models.FloatField(default=0.0)
    owner_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    settings = models.JSONField(default=dict)

    class Meta:
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')

    def __str__(self):
        return self.name

    @property
    def branding(self):
        return {
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'logo_url': self.logo.url if self.logo else None,
            'favicon_url': self.favicon.url if self.favicon else None,
            'font_family': self.font_family,
            'custom_css': self.custom_css,
        }
