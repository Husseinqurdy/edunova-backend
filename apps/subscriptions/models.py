from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class Plan(models.Model):
    class Tier(models.TextChoices):
        STARTER = 'starter', _('Starter')
        PROFESSIONAL = 'professional', _('Professional')
        ENTERPRISE = 'enterprise', _('Enterprise')
        CUSTOM = 'custom', _('Custom')

    class BillingCycle(models.TextChoices):
        MONTHLY = 'monthly', _('Monthly')
        YEARLY = 'yearly', _('Yearly')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=Tier.choices)
    billing_cycle = models.CharField(max_length=10, choices=BillingCycle.choices, default=BillingCycle.MONTHLY)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    price_description = models.CharField(max_length=100, blank=True)
    stripe_price_id = models.CharField(max_length=100, blank=True)

    # Limits
    max_students = models.IntegerField(default=50)
    max_instructors = models.IntegerField(default=5)
    max_courses = models.IntegerField(default=10)
    max_storage_gb = models.FloatField(default=5.0)
    max_admins = models.IntegerField(default=1)
    bandwidth_gb = models.FloatField(default=50.0)

    # Features (True/False flags)
    has_live_classes = models.BooleanField(default=False)
    has_ai_features = models.BooleanField(default=False)
    has_certificates = models.BooleanField(default=False)
    has_blockchain_certs = models.BooleanField(default=False)
    has_custom_branding = models.BooleanField(default=False)
    has_custom_domain = models.BooleanField(default=False)
    has_api_access = models.BooleanField(default=False)
    has_advanced_analytics = models.BooleanField(default=False)
    has_gamification = models.BooleanField(default=False)
    has_marketplace = models.BooleanField(default=False)
    has_mobile_app = models.BooleanField(default=False)
    has_sso = models.BooleanField(default=False)
    has_white_label = models.BooleanField(default=False)
    has_priority_support = models.BooleanField(default=False)
    has_scorm = models.BooleanField(default=False)
    has_multi_language = models.BooleanField(default=True)
    has_bulk_enrollment = models.BooleanField(default=False)
    has_zoom_integration = models.BooleanField(default=False)

    description = models.TextField(blank=True)
    features_list = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'price_usd']
        verbose_name = _('Plan')
        verbose_name_plural = _('Plans')

    def __str__(self):
        return f"{self.name} ({self.get_tier_display()} - ${self.price_usd}/{self.billing_cycle})"


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        CANCELLED = 'cancelled', _('Cancelled')
        PAST_DUE = 'past_due', _('Past Due')
        TRIALING = 'trialing', _('Trialing')
        PAUSED = 'paused', _('Paused')
        EXPIRED = 'expired', _('Expired')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIALING)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')

    def __str__(self):
        return f"Subscription: {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        return self.status in [self.Status.ACTIVE, self.Status.TRIALING]


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')
    stripe_invoice_id = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20)
    invoice_pdf = models.URLField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.id} - ${self.amount}"
