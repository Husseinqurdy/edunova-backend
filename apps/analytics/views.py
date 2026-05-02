from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .models import UserActivity, TenantAnalytics, CourseAnalytics
from apps.courses.models import Course, Enrollment
from apps.accounts.models import User
from django.utils import timezone
from datetime import timedelta


class AnalyticsOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        since = timezone.now() - timedelta(days=days)
        user = request.user

        if user.role in ['tenant_admin', 'super_admin']:
            data = {
                'total_users': User.objects.count(),
                'new_users': User.objects.filter(date_joined__gte=since).count(),
                'total_enrollments': Enrollment.objects.count(),
                'new_enrollments': Enrollment.objects.filter(enrolled_at__gte=since).count(),
                'total_courses': Course.objects.filter(status='published').count(),
                'completions': Enrollment.objects.filter(status='completed', completed_at__gte=since).count(),
                'active_users': UserActivity.objects.filter(created_at__gte=since).values('user').distinct().count(),
                'period_days': days,
            }
        else:
            enrollments = Enrollment.objects.filter(student=user)
            data = {
                'enrolled_courses': enrollments.count(),
                'completed_courses': enrollments.filter(status='completed').count(),
                'average_progress': sum(e.progress_percentage for e in enrollments) / max(enrollments.count(), 1),
                'recent_activity': UserActivity.objects.filter(user=user, created_at__gte=since).count(),
            }
        return Response(data)


class CourseAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role in ['instructor', 'tenant_admin', 'super_admin']:
            if user.role == 'instructor':
                courses = Course.objects.filter(instructor=user)
            else:
                courses = Course.objects.all()

            data = []
            for course in courses[:20]:
                enrollments = Enrollment.objects.filter(course=course)
                data.append({
                    'course_id': str(course.id),
                    'title': course.title,
                    'total_enrollments': enrollments.count(),
                    'completions': enrollments.filter(status='completed').count(),
                    'avg_progress': sum(e.progress_percentage for e in enrollments) / max(enrollments.count(), 1),
                    'avg_rating': course.average_rating,
                    'revenue': float(sum(e.payment_amount for e in enrollments)),
                })
            return Response(data)
        return Response({'error': 'Permission denied'}, status=403)


class UserActivityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        days = int(request.query_params.get('days', 7))
        since = timezone.now() - timedelta(days=days)
        activities = UserActivity.objects.filter(user=user, created_at__gte=since).order_by('-created_at')[:50]
        data = [
            {
                'type': a.activity_type,
                'course': a.course.title if a.course else None,
                'created_at': a.created_at,
                'duration_seconds': a.duration_seconds,
            }
            for a in activities
        ]
        return Response(data)
