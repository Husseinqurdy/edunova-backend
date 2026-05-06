from datetime import timedelta, timezone
import json
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from lms_project.helpers.provision import provision_tenant
from lms_project.models import Institution, Domain
import os
from django.conf import settings
from django_tenants.utils import schema_context
from django.db import connection
from rest_framework.parsers import JSONParser
from core.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model, authenticate
from .permissions import IsSuperAdmin
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from django.db.models import Count
from collections import OrderedDict
from auditlog.models import LogEntry
from .models import NotificationReadStatus, SystemNotification
import jwt
from datetime import datetime
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from lms_project.services.payments import initiate_zenopay_payment
from django.views.decorators.csrf import csrf_exempt
import requests
from dotenv import load_dotenv

load_dotenv()


ZENOPAY_API_KEY = os.getenv("ZENOPAY_API_KEY")


from .serializers import (
    InstitutionRegisterSerializer,
    InstitutionPublicSerializer,
    InstitutionSerializer,
    SignupSerializer,
    LoginSerializer,
    SuperAdminSignupSerializer,
    InstitutionListSerializer,
    AnalyticsSerializer,
    SystemNotificationSerializer,
    
)


class RegisterInstitutionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InstitutionRegisterSerializer(data=request.data)
        if serializer.is_valid():
            client_user = request.user
            plan = serializer.validated_data.get("plan")

            try:
                with schema_context("public"):
                    institution, login_user = provision_tenant(serializer.validated_data, client_user)

                    if plan == "free":
                        institution.is_active = True
                        institution.paid_until = timezone.now().date() + timedelta(days=14)
                    else:
                        institution.is_active = False
                        institution.paid_until = None

                    institution.save()

                response_data = {
                    "message": f"Institution '{institution.name}' registered successfully.",
                    "subdomain": request.data.get("domain", ""),
                    "institution_name": institution.name,
                    "registration_number": institution.registration_number,
                    "password": "admin",
                }

                if plan == "premium":
                    buyer_phone = request.data.get("buyer_phone", "0700000000")
                    payment_response = initiate_zenopay_payment(institution, buyer_phone)
                    if payment_response.get("status_code") == 200:
                        with schema_context("public"):
                            institution.payment_order_id = payment_response.get("order_id")
                            institution.save()
                        response_data["order_id"] = payment_response.get("order_id")
                    else:
                        return Response({"error": "Failed to initiate payment", "details": payment_response}, status=500)

                return Response(response_data, status=status.HTTP_201_CREATED)

            except Exception as e:
                import traceback
                traceback.print_exc()
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class ClientInstitutionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        institutions = Institution.objects.filter(
            owner_email=request.user.email,
            owner_registration_number=request.user.registration_number
        )
        serializer = InstitutionSerializer(institutions, many=True, context={"request": request})
        return Response(serializer.data)


class DeleteInstitutionView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, schema_name):
        try:
            institution = Institution.objects.get(
                schema_name=schema_name,
                owner_email=request.user.email,
                owner_registration_number=request.user.registration_number
            )
            domain = Domain.objects.get(tenant=institution)

            if institution.logo and institution.logo.name:
                logo_path = os.path.join(settings.MEDIA_ROOT, institution.logo.name)
                if os.path.exists(logo_path):
                    os.remove(logo_path)

            connection.set_schema_to_public()
            institution.delete(force_drop=True)
            domain.delete()

            return Response({"message": "Institution and logo deleted successfully."}, status=200)
        except Institution.DoesNotExist:
            return Response({"error": "Institution not found or unauthorized."}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)




class UpdateInstitutionView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def put(self, request, schema_name):
        with schema_context("public"):  # ✅ Fetch institution safely
            try:
                institution = Institution.objects.get(
                    schema_name=schema_name,
                    owner_email=request.user.email,
                    owner_registration_number=request.user.registration_number
                )
            except Institution.DoesNotExist:
                return Response({"error": "Institution not found or unauthorized."}, status=404)

        with schema_context(schema_name):  # ✅ Update inside correct schema
            serializer = InstitutionSerializer(institution, data=request.data, partial=True, context={"request": request})
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Institution updated successfully.", "institution": serializer.data}, status=200)
            return Response(serializer.errors, status=400)


class InstitutionInfoView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            # Accept schema_name from query param (path-based routing)
            schema_name = request.query_params.get('schema') or getattr(request.tenant, 'schema_name', None)
            if not schema_name or schema_name == 'public':
                return Response({"error": "Schema name required."}, status=400)
            institution = Institution.objects.get(schema_name=schema_name)
            serializer = InstitutionPublicSerializer(institution, context={"request": request})
            return Response(serializer.data, status=200)
        except Institution.DoesNotExist:
            return Response({"error": "Institution not found."}, status=404)


class TenantLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        reg_number = request.data.get("registration_number")
        password = request.data.get("password")
        schema_name = request.data.get("schema_name")

        if not reg_number or not password:
            return Response({"error": "Registration number and password required."}, status=400)

        if not schema_name:
            return Response({"error": "schema_name is required."}, status=400)

        try:
            with schema_context(schema_name):
                user = authenticate(request, registration_number=reg_number, password=password)

                if not user:
                    # Try direct lookup as fallback
                    try:
                        user_obj = User.objects.get(registration_number=reg_number)
                        if user_obj.check_password(password):
                            user = user_obj
                    except User.DoesNotExist:
                        pass

                if not user:
                    return Response({"error": "Invalid credentials."}, status=401)

                refresh = RefreshToken.for_user(user)

                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "role": user.role,
                    "username": f"{user.firstname} {user.surname}".strip() if hasattr(user, 'firstname') else user.registration_number,
                    "registration_number": user.registration_number,
                }, status=200)

        except Exception as e:
            return Response({"error": f"Login failed: {str(e)}"}, status=500)
        

User = get_user_model()

# 🔐 Signup for Client
class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(role='client')
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Client registered successfully",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "role": user.role,
                "username": user.username,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 🔐 Signup for SuperAdmin
class SuperAdminSignupView(generics.CreateAPIView):
    serializer_class = SuperAdminSignupSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(role='superadmin')
            return Response({"message": "SuperAdmin registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email and password required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"error": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({"error": "User account is disabled."}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "role": user.role,
            "username": user.username
        })
    

# 🔒 Protected View (for testing JWT)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({"message": f"Hello {request.user.username}, you are authenticated!"})





class SuperAdminInstitutionListView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        institutions = Institution.objects.all().order_by("-created_on")
        serializer = InstitutionListSerializer(institutions, many=True)
        return Response(serializer.data)
    





class SuperAdminAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "superadmin":
            return Response({"detail": "Unauthorized"}, status=403)

        today = now()
        months = OrderedDict()
        for i in reversed(range(6)):
            month = (today.replace(day=1) - timedelta(days=30 * i)).strftime("%b")
            months[month] = {"logins": 0, "institutions": 0}

        for user in User.objects.all():
            m = user.date_joined.strftime("%b")
            if m in months:
                months[m]["logins"] += 1

        for inst in Institution.objects.all():
            m = inst.created_on.strftime("%b")
            if m in months:
                months[m]["institutions"] += 1

        data = [
            {
                "month": m,
                "logins": values["logins"],
                "institutions": values["institutions"],
            }
            for m, values in months.items()
        ]

        return Response(data)
    

class SuperAdminStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "superadmin":
            return Response({"detail": "Unauthorized"}, status=403)

        return Response({
            "total_institutions": Institution.objects.count(),
            "total_users": User.objects.count()
        })


class RenewInstitutionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "superadmin":
            return Response({"detail": "Unauthorized"}, status=403)

        try:
            inst = Institution.objects.get(pk=pk)
            months = int(request.data.get("months", 12))
            inst.paid_until = now().date() + timedelta(days=30 * months)
            inst.save()
            return Response({"detail": "Renewed successfully"})
        except Institution.DoesNotExist:
            return Response({"detail": "Institution not found"}, status=404)
        


class InstitutionDeleteView(generics.DestroyAPIView):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated]


class AuditLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "superadmin":
            return Response({"detail": "Unauthorized"}, status=403)

        logs = LogEntry.objects.select_related("actor").order_by("-timestamp")[:50]
        data = [
            {
                "user": log.actor.email if log.actor else "System",
                "action": log.get_action_display(),
                "schema": log.object_pk,
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M"),
                "ip": log.remote_addr or "N/A",
            }
            for log in logs
        ]
        return Response(data)
    


class SendNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "superadmin":
            return Response({"detail": "Unauthorized"}, status=403)

        serializer = SystemNotificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Notification sent successfully"})
        return Response(serializer.errors, status=400)
    



class TenantListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "superadmin":
            return Response({"detail": "Unauthorized"}, status=403)

        domains = Domain.objects.values_list("domain", flat=True)
        return Response(domains)
    

# You can store settings in DB or cache
SYSTEM_SETTINGS = {
    "maintenance": False,
    "darkMode": False,
    "featureFlags": {
        "jwtViewer": True,
        "simulator": True,
        "auditLogs": True
    }
}

class SystemSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "superadmin":
            return Response({"detail": "Unauthorized"}, status=403)
        return Response(SYSTEM_SETTINGS)

    def patch(self, request):
        for key in request.data:
            if key in SYSTEM_SETTINGS:
                SYSTEM_SETTINGS[key] = request.data[key]
        return Response({"detail": "Settings updated"})
    


class JWTPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "superadmin":
            return Response({"detail": "Unauthorized"}, status=403)

        payload = {
                "email": request.user.email,
                "role": request.user.role,
                "exp": datetime.utcnow() + timedelta(days=7),
            }

        token = jwt.encode(payload, "your-secret-key", algorithm="HS256")
        return Response({"token": token})
    
class ClientNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = SystemNotification.objects.all().order_by("-sent_at")
        serialized = []
        for n in notifications:
            is_read = NotificationReadStatus.objects.filter(
                notification=n,
                user_email=request.user.email
            ).exists()
            serialized.append({
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "created_at": n.sent_at,
                "read": is_read,
            })
        return Response(serialized)


from django.contrib.auth import get_user_model
User = get_user_model()

class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            notification = SystemNotification.objects.get(pk=pk)
            NotificationReadStatus.objects.get_or_create(
                notification=notification,
                user_email=request.user.email
            )
            return Response({"detail": "Marked as read"})
        except SystemNotification.DoesNotExist:
            return Response({"detail": "Notification not found"}, status=404)
        


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "email": user.email,
        })


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        new_password = request.data.get("new_password")
        if not new_password:
            return Response({"error": "New password required"}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password updated successfully"})
    


class ToggleInstitutionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, schema_name):
        if request.user.role != "superadmin":
            return Response({"error": "Forbidden"}, status=403)

        action = request.data.get("action")
        if action not in ["activate", "deactivate"]:
            return Response({"error": "Invalid action"}, status=400)

        with schema_context("public"):  # ✅ Force update inside public schema
            try:
                institution = Institution.objects.get(schema_name=schema_name)

                if action == "activate":
                    institution.is_active = True
                    institution.paid_until = timezone.now().date() + timedelta(days=30)
                else:
                    institution.is_active = False

                institution.save()
                return Response({"detail": f"Institution '{institution.name}' updated"}, status=200)

            except Institution.DoesNotExist:
                return Response({"error": "Institution not found"}, status=404)



class InitiatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, schema_name):
        with schema_context("public"):
            try:
                institution = Institution.objects.get(schema_name=schema_name)

                if institution.plan != "premium":
                    return Response({"error": "Only premium institutions require payment"}, status=400)

                buyer_phone = request.data.get("buyer_phone", "0700000000")  # ✅ fallback if missing

                payment_response = initiate_zenopay_payment(institution, buyer_phone)

                # ✅ Check if Zenopay responded successfully
                if payment_response.get("status_code") == 200:
                    return Response({
                        "message": payment_response.get("message"),
                        "order_id": payment_response.get("order_id")
                    }, status=200)
                else:
                    return Response({
                        "error": "Failed to initiate payment",
                        "details": payment_response
                    }, status=500)

            except Institution.DoesNotExist:
                return Response({"error": "Institution not found"}, status=404)
            

@csrf_exempt
def zenopay_webhook(request):
    if request.headers.get("x-api-key") != settings.ZENOPAY_API_KEY:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    schema = payload.get("metadata", {}).get("schema_name")
    status = payload.get("payment_status")

    if not schema or not status:
        return JsonResponse({"error": "Invalid payload"}, status=400)

    with schema_context("public"):
        try:
            institution = Institution.objects.get(schema_name=schema)

            if status.upper() == "COMPLETED":
                institution.is_active = True
                institution.paid_until = timezone.now().date() + timedelta(days=30)
            else:
                institution.is_active = False

            institution.save()

        except Institution.DoesNotExist:
            return JsonResponse({"error": "Institution not found"}, status=404)

    return JsonResponse({"detail": "Webhook processed"})


class GetInstitutionCredentialsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, schema_name):
        with schema_context("public"):
            try:
                institution = Institution.objects.get(schema_name=schema_name)

                if institution.plan != "premium":
                    return Response({"error": "Only premium institutions require payment verification"}, status=400)

                if not institution.payment_order_id:
                    return Response({"error": "No payment order found for this institution"}, status=404)

                # ✅ Check payment status from Zenopay
                zenopay_url = f"https://zenoapi.com/api/payments/order-status?order_id={institution.payment_order_id}"
                headers = {"x-api-key": ZENOPAY_API_KEY}
                res = requests.get(zenopay_url, headers=headers)

                if res.status_code != 200:
                    return Response({"error": "Failed to contact Zenopay"}, status=502)

                data = res.json()
                payment_status = data.get("payment_status")

                if payment_status == "COMPLETED":
                    institution.is_active = True
                    institution.paid_until = timezone.now().date() + timezone.timedelta(days=365)
                    institution.save()

                    return Response({
                        "reg_number": institution.registration_number,
                        "default_password": "admin"
                    }, status=200)

                return Response({
                    "message": "Payment not completed yet",
                    "status": payment_status
                }, status=202)

            except Institution.DoesNotExist:
                return Response({"error": "Institution not found"}, status=404)