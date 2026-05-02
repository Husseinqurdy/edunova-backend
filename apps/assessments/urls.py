from django.urls import path
from . import views

urlpatterns = [
    path('quizzes/', views.QuizListView.as_view(), name='quiz_list'),
    path('quizzes/<uuid:pk>/', views.QuizDetailView.as_view(), name='quiz_detail'),
    path('quizzes/<uuid:quiz_id>/attempt/', views.StartQuizAttemptView.as_view(), name='start_attempt'),
    path('quizzes/<uuid:quiz_id>/submit/', views.SubmitQuizView.as_view(), name='submit_quiz'),
    path('assignments/', views.AssignmentListView.as_view(), name='assignment_list'),
    path('assignments/<uuid:pk>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignments/<uuid:assignment_id>/submit/', views.SubmitAssignmentView.as_view(), name='submit_assignment'),
]
