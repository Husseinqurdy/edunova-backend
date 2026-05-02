from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid


class Quiz(models.Model):
    class QuizType(models.TextChoices):
        PRACTICE = 'practice', _('Practice Quiz')
        GRADED = 'graded', _('Graded Quiz')
        FINAL = 'final', _('Final Exam')
        SURVEY = 'survey', _('Survey')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.OneToOneField('courses.Lesson', on_delete=models.CASCADE, related_name='quiz', null=True, blank=True)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=300)
    title_translations = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    quiz_type = models.CharField(max_length=20, choices=QuizType.choices, default=QuizType.GRADED)
    time_limit_minutes = models.IntegerField(null=True, blank=True)
    passing_score = models.IntegerField(default=70)
    max_attempts = models.IntegerField(default=3)
    shuffle_questions = models.BooleanField(default=True)
    shuffle_answers = models.BooleanField(default=True)
    show_answers_after = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    class QuestionType(models.TextChoices):
        MCQ = 'mcq', _('Multiple Choice')
        MULTI_SELECT = 'multi_select', _('Multi Select')
        TRUE_FALSE = 'true_false', _('True / False')
        SHORT_ANSWER = 'short_answer', _('Short Answer')
        ESSAY = 'essay', _('Essay')
        FILL_BLANK = 'fill_blank', _('Fill in the Blank')
        MATCHING = 'matching', _('Matching')
        ORDERING = 'ordering', _('Ordering')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QuestionType.choices, default=QuestionType.MCQ)
    text = models.TextField()
    text_translations = models.JSONField(default=dict)
    explanation = models.TextField(blank=True)
    explanation_translations = models.JSONField(default=dict)
    image = models.ImageField(upload_to='questions/', blank=True, null=True)
    points = models.IntegerField(default=1)
    sort_order = models.IntegerField(default=0)
    is_ai_generated = models.BooleanField(default=False)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.quiz.title} - Q{self.sort_order}"


class Answer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    text_translations = models.JSONField(default=dict)
    is_correct = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']


class QuizAttempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', _('In Progress')
        SUBMITTED = 'submitted', _('Submitted')
        GRADED = 'graded', _('Graded')
        TIMED_OUT = 'timed_out', _('Timed Out')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    score = models.FloatField(null=True, blank=True)
    score_percentage = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    time_taken_seconds = models.IntegerField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    answers_data = models.JSONField(default=dict)
    attempt_number = models.IntegerField(default=1)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    browser_info = models.JSONField(default=dict)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.student.email} - {self.quiz.title} - Attempt {self.attempt_number}"


class Assignment(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        CLOSED = 'closed', _('Closed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.OneToOneField('courses.Lesson', on_delete=models.CASCADE, related_name='assignment', null=True, blank=True)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=300)
    description = models.TextField()
    description_translations = models.JSONField(default=dict)
    instructions = models.TextField(blank=True)
    max_score = models.IntegerField(default=100)
    passing_score = models.IntegerField(default=60)
    due_date = models.DateTimeField(null=True, blank=True)
    allow_late_submission = models.BooleanField(default=False)
    late_penalty_percent = models.IntegerField(default=10)
    allowed_file_types = models.JSONField(default=list)
    max_file_size_mb = models.IntegerField(default=10)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PUBLISHED)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', _('Submitted')
        GRADING = 'grading', _('Being Graded')
        GRADED = 'graded', _('Graded')
        RETURNED = 'returned', _('Returned for Revision')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    content = models.TextField(blank=True)
    files = models.JSONField(default=list)
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='graded_submissions'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    is_late = models.BooleanField(default=False)

    class Meta:
        unique_together = ['assignment', 'student']

    def __str__(self):
        return f"{self.student.email} - {self.assignment.title}"
