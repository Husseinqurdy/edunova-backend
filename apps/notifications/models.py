# models.py
from django.db import models
from django.conf import settings
import uuid


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        COURSE_ENROLLED = 'course_enrolled', 'Course Enrolled'
        LESSON_COMPLETED = 'lesson_completed', 'Lesson Completed'
        QUIZ_RESULT = 'quiz_result', 'Quiz Result'
        ASSIGNMENT_GRADED = 'assignment_graded', 'Assignment Graded'
        CERTIFICATE_ISSUED = 'certificate_issued', 'Certificate Issued'
        COURSE_PUBLISHED = 'course_published', 'Course Published'
        PAYMENT_SUCCESS = 'payment_success', 'Payment Success'
        ANNOUNCEMENT = 'announcement', 'Announcement'
        SYSTEM = 'system', 'System'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.title}"
