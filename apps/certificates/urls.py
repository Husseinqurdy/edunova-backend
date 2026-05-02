from django.urls import path
from . import views

urlpatterns = [
    path('', views.CertificateListView.as_view(), name='certificate_list'),
    path('<uuid:pk>/', views.CertificateDetailView.as_view(), name='certificate_detail'),
    path('verify/<str:hash>/', views.VerifyCertificateView.as_view(), name='verify_certificate'),
]
