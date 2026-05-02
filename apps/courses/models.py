from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    name_translations = models.JSONField(default=dict)  # {'sw': 'Sayansi', 'fr': 'Science'}
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#6366f1')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Course(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        REVIEW = 'review', _('Under Review')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')

    class Level(models.TextChoices):
        BEGINNER = 'beginner', _('Beginner')
        INTERMEDIATE = 'intermediate', _('Intermediate')
        ADVANCED = 'advanced', _('Advanced')
        ALL_LEVELS = 'all', _('All Levels')

    class AccessType(models.TextChoices):
        FREE = 'free', _('Free')
        PAID = 'paid', _('Paid')
        SUBSCRIPTION = 'subscription', _('Subscription Only')
        INVITE = 'invite', _('Invite Only')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    title_translations = models.JSONField(default=dict)
    slug = models.SlugField(max_length=350, unique=True)
    description = models.TextField()
    description_translations = models.JSONField(default=dict)
    short_description = models.CharField(max_length=500, blank=True)
    short_description_translations = models.JSONField(default=dict)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses_teaching')
    co_instructors = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='courses_co_teaching')

    thumbnail = models.ImageField(upload_to='courses/thumbnails/', blank=True, null=True)
    preview_video = models.FileField(upload_to='courses/previews/', blank=True, null=True)
    preview_video_url = models.URLField(blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.ALL_LEVELS)
    access_type = models.CharField(max_length=20, choices=AccessType.choices, default=AccessType.FREE)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')

    language = models.CharField(max_length=5, default='en')
    subtitles_languages = models.JSONField(default=list)
    requirements = models.JSONField(default=list)
    requirements_translations = models.JSONField(default=dict)
    what_you_learn = models.JSONField(default=list)
    what_you_learn_translations = models.JSONField(default=dict)
    target_audience = models.JSONField(default=list)

    duration_hours = models.FloatField(default=0)
    total_lectures = models.IntegerField(default=0)
    total_enrollments = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0)
    total_reviews = models.IntegerField(default=0)

    certificate_template = models.ForeignKey(
        'certificates.CertificateTemplate', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='courses'
    )
    has_certificate = models.BooleanField(default=False)
    completion_percentage_required = models.IntegerField(default=80)

    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    tags = models.JSONField(default=list)
    seo_meta = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Module(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=300)
    title_translations = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    is_free_preview = models.BooleanField(default=False)
    duration_minutes = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    class LessonType(models.TextChoices):
        VIDEO = 'video', _('Video')
        DOCUMENT = 'document', _('Document')
        QUIZ = 'quiz', _('Quiz')
        ASSIGNMENT = 'assignment', _('Assignment')
        LIVE = 'live', _('Live Class')
        AUDIO = 'audio', _('Audio')
        SCORM = 'scorm', _('SCORM')
        INTERACTIVE = 'interactive', _('Interactive')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=300)
    title_translations = models.JSONField(default=dict)
    lesson_type = models.CharField(max_length=20, choices=LessonType.choices, default=LessonType.VIDEO)
    content = models.TextField(blank=True)
    content_translations = models.JSONField(default=dict)

    video_file = models.FileField(upload_to='lessons/videos/', blank=True, null=True)
    video_url = models.URLField(blank=True)
    cloudinary_public_id = models.CharField(max_length=200, blank=True)
    document_file = models.FileField(upload_to='lessons/documents/', blank=True, null=True)
    audio_file = models.FileField(upload_to='lessons/audio/', blank=True, null=True)
    scorm_file = models.FileField(upload_to='lessons/scorm/', blank=True, null=True)

    duration_minutes = models.IntegerField(default=0)
    sort_order = models.IntegerField(default=0)
    is_free_preview = models.BooleanField(default=False)
    is_mandatory = models.BooleanField(default=True)
    allow_download = models.BooleanField(default=False)
    subtitles = models.JSONField(default=dict)
    attachments = models.JSONField(default=list)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        COMPLETED = 'completed', _('Completed')
        DROPPED = 'dropped', _('Dropped')
        EXPIRED = 'expired', _('Expired')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    progress_percentage = models.FloatField(default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    certificate_issued = models.BooleanField(default=False)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['student', 'course']

    def __str__(self):
        return f"{self.student.email} -> {self.course.title}"


class LessonProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    watch_time_seconds = models.IntegerField(default=0)
    last_position_seconds = models.IntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['enrollment', 'lesson']


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    is_verified = models.BooleanField(default=True)
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['course', 'student']

    def __str__(self):
        return f"{self.student.email} - {self.course.title} - {self.rating}★"
