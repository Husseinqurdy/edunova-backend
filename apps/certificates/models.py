from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid
import hashlib


class CertificateTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    background_image = models.ImageField(upload_to='certificates/templates/', blank=True, null=True)
    html_template = models.TextField(blank=True)
    css_styles = models.TextField(blank=True)
    primary_color = models.CharField(max_length=7, default='#1e293b')
    secondary_color = models.CharField(max_length=7, default='#6366f1')
    font_family = models.CharField(max_length=100, default='Georgia')
    logo_position = models.CharField(max_length=20, default='top-center')
    signature_image = models.ImageField(upload_to='certificates/signatures/', blank=True, null=True)
    signatory_name = models.CharField(max_length=200, blank=True)
    signatory_title = models.CharField(max_length=200, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.OneToOneField('courses.Enrollment', on_delete=models.CASCADE, related_name='certificate')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='certificates')
    template = models.ForeignKey(CertificateTemplate, on_delete=models.SET_NULL, null=True)
    certificate_number = models.CharField(max_length=100, unique=True)
    verification_hash = models.CharField(max_length=256, unique=True)
    blockchain_tx_hash = models.CharField(max_length=256, blank=True)
    blockchain_network = models.CharField(max_length=50, blank=True)
    is_blockchain_verified = models.BooleanField(default=False)
    pdf_file = models.FileField(upload_to='certificates/pdfs/', blank=True, null=True)
    cloudinary_url = models.URLField(blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_valid = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            self.certificate_number = f"CERT-{str(self.id)[:8].upper()}"
        if not self.verification_hash:
            data = f"{self.student_id}{self.course_id}{self.issued_at}"
            self.verification_hash = hashlib.sha256(data.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Certificate: {self.student.get_full_name()} - {self.course.title}"

    @property
    def verification_url(self):
        return f"/verify/{self.verification_hash}"
