from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Certificate, CertificateTemplate
from .serializers import CertificateSerializer, CertificateTemplateSerializer


class CertificateListView(generics.ListAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Certificate.objects.filter(student=self.request.user, is_valid=True)


class CertificateDetailView(generics.RetrieveAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Certificate.objects.filter(student=self.request.user)


class VerifyCertificateView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, hash):
        try:
            cert = Certificate.objects.get(verification_hash=hash, is_valid=True)
            return Response({
                'valid': True,
                'certificate_number': cert.certificate_number,
                'student_name': cert.student.get_full_name(),
                'course_title': cert.course.title,
                'issued_at': cert.issued_at,
                'expires_at': cert.expires_at,
                'blockchain_verified': cert.is_blockchain_verified,
                'blockchain_tx': cert.blockchain_tx_hash,
            })
        except Certificate.DoesNotExist:
            return Response({'valid': False, 'message': 'Certificate not found or invalid.'}, status=404)
