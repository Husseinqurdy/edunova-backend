from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Auth
    path('api/v1/auth/', include('apps.accounts.urls')),
    # Superadmin tenant management
    path('api/v1/tenants/', include('apps.tenants.urls')),
    # Subscriptions
    path('api/v1/subscriptions/', include('apps.subscriptions.urls')),
    # Courses
    path('api/v1/courses/', include('apps.courses.urls')),
    # Assessments
    path('api/v1/assessments/', include('apps.assessments.urls')),
    # Certificates
    path('api/v1/certificates/', include('apps.certificates.urls')),
    # Analytics
    path('api/v1/analytics/', include('apps.analytics.urls')),
    # Notifications
    path('api/v1/notifications/', include('apps.notifications.urls')),
    # Tenant branding (works on public schema too for dev)
    path('api/v1/tenant/', include('apps.tenants.tenant_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
