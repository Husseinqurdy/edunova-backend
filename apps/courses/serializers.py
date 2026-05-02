from rest_framework import serializers
from .models import Category, Course, Module, Lesson, Enrollment, LessonProgress, Review
from apps.accounts.serializers import UserSerializer


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    course_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'name_translations', 'slug', 'description',
                  'icon', 'color', 'parent', 'children', 'course_count', 'sort_order']

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []

    def get_course_count(self, obj):
        return obj.courses.filter(status='published').count()


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'title_translations', 'lesson_type', 'content',
                  'content_translations', 'video_url', 'cloudinary_public_id',
                  'duration_minutes', 'sort_order', 'is_free_preview',
                  'is_mandatory', 'allow_download', 'subtitles', 'attachments']
        extra_kwargs = {
            'video_file': {'write_only': True},
            'document_file': {'write_only': True},
        }


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    lesson_count = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ['id', 'title', 'title_translations', 'description',
                  'sort_order', 'is_free_preview', 'duration_minutes',
                  'lessons', 'lesson_count']

    def get_lesson_count(self, obj):
        return obj.lessons.count()


class ReviewSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'student_name', 'student_avatar',
                  'helpful_count', 'created_at']
        read_only_fields = ['id', 'student_name', 'student_avatar', 'helpful_count', 'created_at']

    def get_student_name(self, obj):
        return obj.student.get_full_name()

    def get_student_avatar(self, obj):
        if obj.student.avatar:
            return obj.student.avatar.url
        return None


class CourseListSerializer(serializers.ModelSerializer):
    instructor_name = serializers.SerializerMethodField()
    instructor_avatar = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'title_translations', 'slug', 'short_description',
                  'short_description_translations', 'thumbnail_url', 'level', 'language',
                  'access_type', 'price', 'discounted_price', 'currency',
                  'duration_hours', 'total_lectures', 'total_enrollments',
                  'average_rating', 'total_reviews', 'is_featured', 'is_bestseller',
                  'instructor_name', 'instructor_avatar', 'category_name', 'is_enrolled',
                  'has_certificate', 'tags', 'status', 'created_at']

    def get_instructor_name(self, obj):
        return obj.instructor.get_full_name()

    def get_instructor_avatar(self, obj):
        if obj.instructor.avatar:
            return obj.instructor.avatar.url
        return None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return None

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Enrollment.objects.filter(student=request.user, course=obj).exists()
        return False


class CourseDetailSerializer(CourseListSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    enrollment_info = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + [
            'description', 'description_translations', 'requirements',
            'what_you_learn', 'target_audience', 'modules',
            'reviews', 'enrollment_info', 'completion_percentage_required',
            'subtitles_languages', 'published_at'
        ]

    def get_reviews(self, obj):
        reviews = obj.reviews.all()[:10]
        return ReviewSerializer(reviews, many=True).data

    def get_enrollment_info(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = Enrollment.objects.get(student=request.user, course=obj)
                return {
                    'enrolled': True,
                    'progress': enrollment.progress_percentage,
                    'status': enrollment.status,
                    'enrolled_at': enrollment.enrolled_at,
                    'certificate_issued': enrollment.certificate_issued,
                }
            except Enrollment.DoesNotExist:
                pass
        return {'enrolled': False}


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    course_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'course', 'course_id', 'status', 'progress_percentage',
                  'enrolled_at', 'completed_at', 'last_accessed', 'certificate_issued']
        read_only_fields = ['id', 'status', 'progress_percentage', 'enrolled_at']


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ['id', 'lesson', 'is_completed', 'watch_time_seconds',
                  'last_position_seconds', 'completed_at', 'notes']
