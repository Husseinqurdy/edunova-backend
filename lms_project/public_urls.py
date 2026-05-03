from django.urls import path
from .views import (
    AuditLogView,
    ChangePasswordView,
    GetInstitutionCredentialsView,
    InitiatePaymentView,
    ProfileView,
    SuperAdminInstitutionListView,
    SuperAdminStatsView,
    SuperAdminAnalyticsView,
    RenewInstitutionView,
    InstitutionDeleteView,
    RegisterInstitutionView,
    SendNotificationView,
    TenantListView,
    SystemSettingsView,
    JWTPreviewView,
    ClientNotificationView,
    MarkNotificationReadView,
    ToggleInstitutionStatusView,
    zenopay_webhook,
    SignupView,
    LoginView,
    SuperAdminSignupView,
    TenantLoginView,
    ClientInstitutionListView,
    InstitutionInfoView,
)

urlpatterns = [
    # ── Auth ──────────────────────────────
    path('auth/signup/', SignupView.as_view()),
    path('auth/login/', LoginView.as_view()),
    path('auth/tenant/login/', TenantLoginView.as_view()),
    path('superadmin/create-superadmin/', SuperAdminSignupView.as_view()),

    # ── Client ────────────────────────────
    path('client/register-institution/', RegisterInstitutionView.as_view()),
    path('client/institution/', ClientInstitutionListView.as_view()),
    path('client/institution/delete/', InstitutionDeleteView.as_view()),
    path('client/profile/', ProfileView.as_view()),
    path('client/change-password/', ChangePasswordView.as_view()),
    path('client/notifications/', ClientNotificationView.as_view()),
    path('client/notifications/mark-read/', MarkNotificationReadView.as_view()),

    # ── Tenant info ───────────────────────
    path('tenant/institution-info/', InstitutionInfoView.as_view()),

    # ── Superadmin ────────────────────────
    path('superadmin/stats/', SuperAdminStatsView.as_view()),
    path('superadmin/institutions/', SuperAdminInstitutionListView.as_view()),
    path('superadmin/analytics/', SuperAdminAnalyticsView.as_view()),
    path('superadmin/send-notification/', SendNotificationView.as_view()),
    path('superadmin/institution/<str:schema_name>/toggle/', ToggleInstitutionStatusView.as_view()),
    path('superadmin/payments/institution/<str:schema_name>/initiate-payment/', InitiatePaymentView.as_view()),
    path('superadmin/order/institution/<str:schema_name>/credentials/', GetInstitutionCredentialsView.as_view()),
    path('superadmin/institutions/<int:pk>/renew/', RenewInstitutionView.as_view()),
    path('superadmin/institutions/<int:pk>/', InstitutionDeleteView.as_view()),

    # ── Misc ──────────────────────────────
    path('audit-logs/', AuditLogView.as_view()),
    path('tenants/', TenantListView.as_view()),
    path('settings/', SystemSettingsView.as_view()),
    path('zenopay/webhook/', zenopay_webhook),
]
