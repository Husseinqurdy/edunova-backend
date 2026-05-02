from django.urls import path
from . import views

urlpatterns = [
    path('info/', views.PublicTenantInfoView.as_view(), name='tenant_info'),
    path('branding/', views.TenantBrandingView.as_view(), name='tenant_branding'),
]
