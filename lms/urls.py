from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('lms_project.public_urls')),
    path('lms/', include('core.urls')),
]
