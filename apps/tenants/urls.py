from django.urls import path
from . import views

# Public schema - superadmin manages tenants
urlpatterns = [
    path('', views.TenantListCreateView.as_view(), name='tenant_list'),
    path('<slug:slug>/', views.TenantDetailView.as_view(), name='tenant_detail'),
    path('stats/overview/', views.SuperAdminStatsView.as_view(), name='superadmin_stats'),
]
