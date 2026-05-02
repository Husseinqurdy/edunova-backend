from django.urls import path
from . import views
urlpatterns = [
    path('overview/', views.AnalyticsOverviewView.as_view(), name='analytics_overview'),
    path('courses/', views.CourseAnalyticsView.as_view(), name='course_analytics'),
    path('users/', views.UserActivityView.as_view(), name='user_activity'),
]
