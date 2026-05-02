from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='category')
router.register('', views.CourseViewSet, basename='course')

urlpatterns = [
    path('', include(router.urls)),
    path('<slug:course_slug>/modules/', views.ModuleViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<slug:course_slug>/modules/<uuid:pk>/', views.ModuleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('enrollments/', views.EnrollmentViewSet.as_view({'get': 'list'})),
]
