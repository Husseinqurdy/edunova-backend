from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import Quiz, Question, Answer, QuizAttempt, Assignment, AssignmentSubmission
from .serializers import (
    QuizSerializer, QuizDetailSerializer, QuizAttemptSerializer,
    AssignmentSerializer, AssignmentSubmissionSerializer
)


class QuizListView(generics.ListAPIView):
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.request.query_params.get('course')
        qs = Quiz.objects.filter(is_active=True)
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


class QuizDetailView(generics.RetrieveAPIView):
    serializer_class = QuizDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Quiz.objects.filter(is_active=True)


class StartQuizAttemptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, quiz_id):
        quiz = Quiz.objects.get(id=quiz_id)
        user = request.user

        # Check max attempts
        attempt_count = QuizAttempt.objects.filter(quiz=quiz, student=user).count()
        if quiz.max_attempts and attempt_count >= quiz.max_attempts:
            return Response({'error': 'Maximum attempts reached.'}, status=status.HTTP_400_BAD_REQUEST)

        attempt = QuizAttempt.objects.create(
            quiz=quiz, student=user, attempt_number=attempt_count + 1,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return Response(QuizAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


class SubmitQuizView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, quiz_id):
        quiz = Quiz.objects.get(id=quiz_id)
        attempt = QuizAttempt.objects.filter(
            quiz=quiz, student=request.user, status='in_progress'
        ).last()

        if not attempt:
            return Response({'error': 'No active attempt found.'}, status=status.HTTP_404_NOT_FOUND)

        answers_data = request.data.get('answers', {})
        total_points = 0
        earned_points = 0

        for question in quiz.questions.all():
            q_id = str(question.id)
            total_points += question.points
            submitted = answers_data.get(q_id, [])

            if question.question_type in ['mcq', 'true_false']:
                correct_answers = list(question.answers.filter(is_correct=True).values_list('id', flat=True))
                correct_ids = [str(a) for a in correct_answers]
                if isinstance(submitted, list):
                    if set(submitted) == set(correct_ids):
                        earned_points += question.points
                else:
                    if submitted in correct_ids:
                        earned_points += question.points
            elif question.question_type == 'multi_select':
                correct_ids = set(str(a.id) for a in question.answers.filter(is_correct=True))
                if set(submitted) == correct_ids:
                    earned_points += question.points

        score_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        passed = score_percentage >= quiz.passing_score

        attempt.status = 'graded'
        attempt.score = earned_points
        attempt.score_percentage = score_percentage
        attempt.passed = passed
        attempt.submitted_at = timezone.now()
        attempt.answers_data = answers_data
        attempt.time_taken_seconds = int((timezone.now() - attempt.started_at).total_seconds())
        attempt.save()

        return Response({
            'score': earned_points,
            'total_points': total_points,
            'score_percentage': round(score_percentage, 1),
            'passed': passed,
            'passing_score': quiz.passing_score,
        })


class AssignmentListView(generics.ListAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.request.query_params.get('course')
        qs = Assignment.objects.filter(status='published')
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


class AssignmentDetailView(generics.RetrieveAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Assignment.objects.all()


class SubmitAssignmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, assignment_id):
        assignment = Assignment.objects.get(id=assignment_id)
        user = request.user

        if AssignmentSubmission.objects.filter(assignment=assignment, student=user).exists():
            return Response({'error': 'Already submitted.'}, status=status.HTTP_400_BAD_REQUEST)

        is_late = assignment.due_date and timezone.now() > assignment.due_date
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            student=user,
            content=request.data.get('content', ''),
            files=request.data.get('files', []),
            is_late=is_late
        )
        return Response(AssignmentSubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)
