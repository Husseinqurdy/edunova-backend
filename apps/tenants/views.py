from rest_framework import serializers, generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Tenant
from apps.subscriptions.models import Plan, Subscription
from django.utils import timezone
from datetime import timedelta


class TenantBrandingSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    favicon_url = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = ['name', 'slug', 'primary_color', 'secondary_color', 'accent_color',
                  'text_color', 'background_color', 'font_family', 'custom_css',
                  'logo_url', 'favicon_url', 'default_language', 'supported_languages']

    def get_logo_url(self, obj):
        try:
            return obj.logo.url if obj.logo else None
        except Exception:
            return None

    def get_favicon_url(self, obj):
        try:
            return obj.favicon.url if obj.favicon else None
        except Exception:
            return None


class TenantSerializer(serializers.ModelSerializer):
    branding = serializers.SerializerMethodField()
    subscription_info = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    course_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'tenant_type', 'status', 'description',
                  'website', 'email', 'phone', 'country', 'timezone',
                  'default_language', 'supported_languages', 'custom_domain',
                  'max_students', 'max_instructors', 'max_storage_gb', 'used_storage_gb',
                  'owner_email', 'created_at', 'trial_ends_at', 'settings',
                  'branding', 'subscription_info', 'student_count', 'course_count']
        read_only_fields = ['id', 'created_at']

    def get_branding(self, obj):
        return obj.branding

    def get_subscription_info(self, obj):
        if obj.subscription:
            return {
                'plan': obj.subscription.plan.name,
                'tier': obj.subscription.plan.tier,
                'status': obj.subscription.status,
                'period_end': obj.subscription.current_period_end,
            }
        return None

    def get_student_count(self, obj):
        from apps.accounts.models import User
        return User.objects.filter(role='student').count()

    def get_course_count(self, obj):
        from apps.courses.models import Course
        return Course.objects.filter(status='published').count()


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'super_admin'


class TenantListCreateView(generics.ListCreateAPIView):
    serializer_class = TenantSerializer
    permission_classes = [IsSuperAdmin]
    queryset = Tenant.objects.all().select_related('subscription__plan')


class TenantDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TenantSerializer
    permission_classes = [IsSuperAdmin]
    queryset = Tenant.objects.all()
    lookup_field = 'slug'


class TenantBrandingView(generics.RetrieveUpdateAPIView):
    serializer_class = TenantBrandingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Return first tenant or create default
        tenant = Tenant.objects.first()
        if not tenant:
            tenant = Tenant.objects.create(
                name='EduNova LMS',
                slug='default',
            )
        return tenant


class PublicTenantInfoView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        tenant = Tenant.objects.first()
        if tenant:
            return Response(TenantBrandingSerializer(tenant).data)
        # Return default branding
        return Response({
            'name': 'EduNova LMS',
            'slug': 'default',
            'primary_color': '#6366f1',
            'secondary_color': '#8b5cf6',
            'accent_color': '#06b6d4',
            'text_color': '#1e293b',
            'background_color': '#ffffff',
            'font_family': 'DM Sans',
            'custom_css': '',
            'logo_url': None,
            'favicon_url': None,
            'default_language': 'en',
            'supported_languages': ['en', 'sw', 'fr'],
        })


class SuperAdminStatsView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        from apps.accounts.models import User
        from apps.subscriptions.models import Subscription

        tenants = Tenant.objects.all()
        active_subs = Subscription.objects.filter(status__in=['active', 'trialing'])

        return Response({
            'total_tenants': tenants.count(),
            'active_tenants': tenants.filter(status='active').count(),
            'trial_tenants': tenants.filter(status='trial').count(),
            'suspended_tenants': tenants.filter(status='suspended').count(),
            'active_subscriptions': active_subs.count(),
            'total_users': User.objects.count(),
            'total_revenue': float(sum(
                s.plan.price_usd for s in active_subs if s.status == 'active'
            )),
            'tenants_by_type': {
                t: tenants.filter(tenant_type=t).count()
                for t in ['school', 'corporate', 'bootcamp', 'ngo', 'individual']
            }
        })
