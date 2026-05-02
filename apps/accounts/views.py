from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone
from .models import User, UserProfile
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'message': 'Account created successfully.'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Simple logout - just return success (token expires naturally)
        return Response({'message': 'Logged out successfully.'})


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Incorrect current password.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully.'})


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['super_admin', 'tenant_admin']:
            return User.objects.all().select_related('profile')
        return User.objects.none()


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all().select_related('profile')
    permission_classes = [permissions.IsAuthenticated]


class DashboardStatsView(APIView):
    def get(self, request):
        user = request.user
        from apps.courses.models import Enrollment, Course
        from apps.certificates.models import Certificate

        data = {
            'role': user.role,
            'full_name': user.get_full_name(),
            'preferred_language': user.preferred_language,
        }

        if user.role == 'student':
            enrollments = Enrollment.objects.filter(student=user)
            data.update({
                'total_enrollments': enrollments.count(),
                'completed_courses': enrollments.filter(status='completed').count(),
                'in_progress': enrollments.filter(status='active').count(),
                'certificates': Certificate.objects.filter(student=user).count(),
                'total_points': getattr(user.profile, 'total_points', 0) if hasattr(user, 'profile') else 0,
                'streak_days': getattr(user.profile, 'streak_days', 0) if hasattr(user, 'profile') else 0,
            })
        elif user.role in ['instructor', 'tenant_admin', 'super_admin']:
            if user.role == 'instructor':
                courses = Course.objects.filter(instructor=user)
            else:
                courses = Course.objects.all()
            total_students = Enrollment.objects.filter(
                course__in=courses
            ).values('student').distinct().count()
            data.update({
                'total_courses': courses.count(),
                'published_courses': courses.filter(status='published').count(),
                'total_students': total_students,
                'total_revenue': float(sum(
                    e.payment_amount for e in Enrollment.objects.filter(course__in=courses)
                )),
            })

        return Response(data)
