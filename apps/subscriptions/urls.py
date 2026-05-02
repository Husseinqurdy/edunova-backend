from django.urls import path
from . import views

urlpatterns = [
    path('plans/', views.PlanListView.as_view(), name='plan_list'),
    path('plans/<uuid:pk>/', views.PlanDetailView.as_view(), name='plan_detail'),
    path('plans/manage/', views.PlanManageView.as_view(), name='plan_manage'),
    path('plans/manage/<uuid:pk>/', views.PlanManageDetailView.as_view(), name='plan_manage_detail'),
    path('current/', views.CurrentSubscriptionView.as_view(), name='current_subscription'),
    path('upgrade/', views.UpgradeSubscriptionView.as_view(), name='upgrade_subscription'),
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
]
