from django.contrib import admin
from django.urls import path, include
from django.conf import settings

# PUBLIC schema URLs (main domain)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('lms_project.public_urls')),
]
