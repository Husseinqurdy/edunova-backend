from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from .models import Category, Course, Module, Lesson, Enrollment, LessonProgress, Review
from .serializers import (
    CategorySerializer, CourseListSerializer, CourseDetailSerializer,
    ModuleSerializer, LessonSerializer, EnrollmentSerializer,
    LessonProgressSerializer, ReviewSerializer
)


class IsTenantAdminOrInstructor(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role in ['super_admin', 'tenant_admin', 'instructor']


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.filter(is_active=True, parent=None)
    serializer_class = CategorySerializer
    permission_classes = [IsTenantAdminOrInstructor]
    lookup_field = 'slug'


class CourseViewSet(ModelViewSet):
    permission_classes = [IsTenantAdminOrInstructor]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'language', 'access_type', 'status', 'category__slug', 'is_featured']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'total_enrollments', 'average_rating', 'price']
    ordering = ['-created_at']
    lookup_field = 'slug'

    def get_queryset(self):
        user = self.request.user
        qs = Course.objects.select_related('instructor', 'category').prefetch_related('modules')
        if not user.is_authenticated or user.role == 'student':
            return qs.filter(status='published')
        if user.role == 'instructor':
            return qs.filter(Q(status='published') | Q(instructor=user))
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseListSerializer

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

    @action(detail=True, methods=['post'])
    def enroll(self, request, slug=None):
        course = self.get_object()
        user = request.user
        if Enrollment.objects.filter(student=user, course=course).exists():
            return Response({'error': 'Already enrolled.'}, status=status.HTTP_400_BAD_REQUEST)
        enrollment = Enrollment.objects.create(student=user, course=course)
        course.total_enrollments += 1
        course.save(update_fields=['total_enrollments'])
        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def review(self, request, slug=None):
        course = self.get_object()
        user = request.user
        if not Enrollment.objects.filter(student=user, course=course).exists():
            return Response({'error': 'Must be enrolled to review.'}, status=status.HTTP_403_FORBIDDEN)
        review, created = Review.objects.update_or_create(
            course=course, student=user,
            defaults={'rating': request.data.get('rating'), 'comment': request.data.get('comment')}
        )
        # Update course average rating
        reviews = Review.objects.filter(course=course)
        course.average_rating = sum(r.rating for r in reviews) / reviews.count()
        course.total_reviews = reviews.count()
        course.save(update_fields=['average_rating', 'total_reviews'])
        return Response(ReviewSerializer(review).data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        courses = Course.objects.filter(status='published', is_featured=True)[:8]
        return Response(CourseListSerializer(courses, many=True, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def my_courses(self, request):
        if request.user.role in ['instructor', 'tenant_admin', 'super_admin']:
            courses = Course.objects.filter(instructor=request.user)
        else:
            enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
            courses = [e.course for e in enrollments]
        return Response(CourseListSerializer(courses, many=True, context={'request': request}).data)


class ModuleViewSet(ModelViewSet):
    serializer_class = ModuleSerializer
    permission_classes = [IsTenantAdminOrInstructor]

    def get_queryset(self):
        return Module.objects.filter(course__slug=self.kwargs.get('course_slug'))

    def perform_create(self, serializer):
        course = Course.objects.get(slug=self.kwargs['course_slug'])
        serializer.save(course=course)


class LessonViewSet(ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Lesson.objects.filter(module__id=self.kwargs.get('module_pk'))

    @action(detail=True, methods=['post'])
    def update_progress(self, request, **kwargs):
        lesson = self.get_object()
        enrollment = Enrollment.objects.get(
            student=request.user,
            course=lesson.module.course
        )
        progress, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment, lesson=lesson
        )
        progress.watch_time_seconds = request.data.get('watch_time_seconds', progress.watch_time_seconds)
        progress.last_position_seconds = request.data.get('last_position_seconds', 0)

        if request.data.get('is_completed') and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()

            # Recalculate course progress
            total_lessons = Lesson.objects.filter(
                module__course=lesson.module.course, is_mandatory=True
            ).count()
            completed = LessonProgress.objects.filter(
                enrollment=enrollment, is_completed=True,
                lesson__is_mandatory=True
            ).count()
            if total_lessons > 0:
                enrollment.progress_percentage = (completed / total_lessons) * 100
                if enrollment.progress_percentage >= lesson.module.course.completion_percentage_required:
                    enrollment.status = 'completed'
                    enrollment.completed_at = timezone.now()
                enrollment.save()

        progress.save()
        return Response(LessonProgressSerializer(progress).data)


class EnrollmentViewSet(ModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user).select_related('course')
