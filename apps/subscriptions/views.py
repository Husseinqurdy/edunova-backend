from rest_framework import serializers, generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Plan, Subscription, Invoice


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'tier', 'billing_cycle', 'price_usd', 'price_description',
            'max_students', 'max_instructors', 'max_courses', 'max_storage_gb',
            'max_admins', 'bandwidth_gb',
            'has_live_classes', 'has_ai_features', 'has_certificates',
            'has_blockchain_certs', 'has_custom_branding', 'has_custom_domain',
            'has_api_access', 'has_advanced_analytics', 'has_gamification',
            'has_marketplace', 'has_mobile_app', 'has_sso', 'has_white_label',
            'has_priority_support', 'has_scorm', 'has_multi_language',
            'has_bulk_enrollment', 'has_zoom_integration',
            'description', 'features_list', 'is_active', 'is_popular', 'sort_order'
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'status', 'current_period_start',
                  'current_period_end', 'trial_start', 'trial_end',
                  'cancel_at_period_end', 'created_at']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'amount', 'currency', 'status', 'invoice_pdf', 'paid_at', 'created_at']


class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Plan.objects.filter(is_active=True).order_by('sort_order', 'price_usd')


class PlanDetailView(generics.RetrieveAPIView):
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Plan.objects.filter(is_active=True)


class CurrentSubscriptionView(APIView):
    def get(self, request):
        from django_tenants.utils import get_current_tenant
        tenant = get_current_tenant()
        if not tenant or not tenant.subscription:
            return Response({'subscription': None})
        return Response(SubscriptionSerializer(tenant.subscription).data)


class UpgradeSubscriptionView(APIView):
    def post(self, request):
        plan_id = request.data.get('plan_id')
        payment_method = request.data.get('payment_method', 'stripe')
        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

        from django_tenants.utils import get_current_tenant
        tenant = get_current_tenant()

        if payment_method == 'stripe' and plan.stripe_price_id:
            # Stripe integration logic would go here
            return Response({
                'message': 'Redirect to Stripe',
                'plan': PlanSerializer(plan).data,
                'redirect_url': f'/checkout/stripe/{plan.id}/'
            })

        return Response({
            'message': 'Subscription upgrade initiated',
            'plan': PlanSerializer(plan).data
        })


class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        from django_tenants.utils import get_current_tenant
        tenant = get_current_tenant()
        if tenant and tenant.subscription:
            return Invoice.objects.filter(subscription=tenant.subscription)
        return Invoice.objects.none()


# Superadmin plan management
class PlanManageView(generics.ListCreateAPIView):
    serializer_class = PlanSerializer
    queryset = Plan.objects.all()

    def get_permissions(self):
        from apps.tenants.views import IsSuperAdmin
        return [IsSuperAdmin()]


class PlanManageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlanSerializer
    queryset = Plan.objects.all()

    def get_permissions(self):
        from apps.tenants.views import IsSuperAdmin
        return [IsSuperAdmin()]
