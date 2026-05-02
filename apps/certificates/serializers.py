from rest_framework import serializers
from .models import Certificate, CertificateTemplate


class CertificateTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateTemplate
        fields = ['id', 'name', 'primary_color', 'secondary_color',
                  'font_family', 'signatory_name', 'signatory_title', 'is_default']


class CertificateSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    course_title = serializers.SerializerMethodField()
    course_thumbnail = serializers.SerializerMethodField()
    verification_url = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = ['id', 'certificate_number', 'verification_hash', 'verification_url',
                  'student_name', 'course_title', 'course_thumbnail',
                  'cloudinary_url', 'issued_at', 'expires_at', 'is_valid',
                  'is_blockchain_verified', 'blockchain_tx_hash']

    def get_student_name(self, obj):
        return obj.student.get_full_name()

    def get_course_title(self, obj):
        return obj.course.title

    def get_course_thumbnail(self, obj):
        if obj.course.thumbnail:
            return obj.course.thumbnail.url
        return None

    def get_verification_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/v1/certificates/verify/{obj.verification_hash}/')
        return obj.verification_url
