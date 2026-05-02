from rest_framework import serializers
from .models import Quiz, Question, Answer, QuizAttempt, Assignment, AssignmentSubmission


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'text_translations', 'sort_order']


class AnswerWithCorrectSerializer(AnswerSerializer):
    class Meta(AnswerSerializer.Meta):
        fields = AnswerSerializer.Meta.fields + ['is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'question_type', 'text', 'text_translations',
                  'image', 'points', 'sort_order', 'answers']


class QuizSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'title_translations', 'description', 'quiz_type',
                  'time_limit_minutes', 'passing_score', 'max_attempts',
                  'shuffle_questions', 'shuffle_answers', 'question_count', 'is_active']

    def get_question_count(self, obj):
        return obj.questions.count()


class QuizDetailSerializer(QuizSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(QuizSerializer.Meta):
        fields = QuizSerializer.Meta.fields + ['questions', 'show_answers_after']


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'status', 'score', 'score_percentage', 'passed',
                  'time_taken_seconds', 'started_at', 'submitted_at', 'attempt_number']


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'description_translations',
                  'instructions', 'max_score', 'passing_score', 'due_date',
                  'allow_late_submission', 'allowed_file_types', 'max_file_size_mb', 'status']


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'assignment', 'status', 'content', 'files',
                  'score', 'feedback', 'submitted_at', 'graded_at', 'is_late']
