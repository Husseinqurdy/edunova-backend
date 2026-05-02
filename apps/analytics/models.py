from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid


class CourseAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.OneToOneField('courses.Course', on_delete=models.CASCADE, related_name='analytics')
    total_views = models.IntegerField(default=0)
    total_enrollments = models.IntegerField(default=0)
    total_completions = models.IntegerField(default=0)
    completion_rate = models.FloatField(default=0)
    average_progress = models.FloatField(default=0)
    average_rating = models.FloatField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_watch_time_minutes = models.FloatField(default=0)
    drop_off_data = models.JSONField(default=dict)
    daily_stats = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics: {self.course.title}"


class UserActivity(models.Model):
    class ActivityType(models.TextChoices):
        LOGIN = 'login', _('Login')
        LESSON_VIEW = 'lesson_view', _('Lesson View')
        LESSON_COMPLETE = 'lesson_complete', _('Lesson Complete')
        QUIZ_ATTEMPT = 'quiz_attempt', _('Quiz Attempt')
        ASSIGNMENT_SUBMIT = 'assignment_submit', _('Assignment Submit')
        COURSE_ENROLL = 'course_enroll', _('Course Enroll')
        COURSE_COMPLETE = 'course_complete', _('Course Complete')
        CERTIFICATE_EARN = 'certificate_earn', _('Certificate Earned')
        FORUM_POST = 'forum_post', _('Forum Post')
        LIVE_CLASS = 'live_class', _('Live Class')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.JSONField(default=dict)
    duration_seconds = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
        ]


class TenantAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    new_enrollments = models.IntegerField(default=0)
    completions = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_watch_minutes = models.IntegerField(default=0)
    quiz_attempts = models.IntegerField(default=0)
    certificates_issued = models.IntegerField(default=0)

    class Meta:
        unique_together = ['date']
        ordering = ['-date']
