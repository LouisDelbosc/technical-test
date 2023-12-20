from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import timedelta
import json

from session_system.token_authentication_middleware import token_auth
from .models import User, Device, Session


def session_serializer(session):
    device_data = {
        "uuid": str(session.device),
        "type": session.device.type,
    }

    # Conditionally add 'vendor_uuid' if device type is 'mobi'
    if session.device.type == "mobi":
        device_data["vendor_uuid"] = str(session.device.vendor_uuid)

    return {
        "uuid": str(session),
        "token": session.token,
        "status": session.status,
        "is_new_user": session.is_new_user,
        "is_new_device": session.is_new_device,
        "user": {
            "uuid": str(session.user),
            "email": session.user.email,
        },
        "device": device_data,
    }


def get_alive_session(user, device):
    session = Session.objects.filter(user=user, device=device).latest("created_at")
    if device.type == "mobi":
        return session
    if timezone.now() - session.created_at > timedelta(hours=2):
        session.status = "expired"
        session.save()
        raise Session.DoesNotExist
    return session


@require_http_methods(["POST"])
def create_session(request, *args, **kwargs):
    try:
        data = json.loads(request.body)
        user_email = data.get("user", {}).get("email")
        device_type = data.get("device", {}).get("type")
        device_vendor = data.get("device", {}).get("vendor_uuid")

        if (
            not user_email
            or not device_type
            or (device_type == "mobi" and not device_vendor)
        ):
            return JsonResponse({"error": "Invalid data"}, status=400)
        user, user_created = User.objects.get_or_create(email=user_email)
        device, device_created = Device.objects.get_or_create(
            user=user, type=device_type, vendor_uuid=device_vendor
        )

        # Create a new Session
        try:
            session = get_alive_session(user, device)
            print(f"OTP CODE: {session.otp_code}")
            return JsonResponse(session_serializer(session), status=200)
        except Session.DoesNotExist:
            session = Session.objects.create(
                user=user,
                device=device,
                is_new_user=user_created,
                is_new_device=device_created,
            )
            print(f"OTP CODE: {session.otp_code}")
            return JsonResponse(session_serializer(session), status=201)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)


@require_http_methods(["PATCH", "PUT"])
@token_auth
def update_session(request, uuid):
    try:
        data = json.loads(request.body)
        otp_code = data.get("otp_code")
        session = Session.objects.get(uuid=uuid)

        # Check if the request is made within 5 minutes of session creation
        if timezone.now() - session.created_at > timedelta(minutes=5):
            session.status = "expired"
            session.save()
            return JsonResponse({"error": "Session expired"}, status=401)

        # Verify OTP code
        if session.otp_code == otp_code:
            session.status = "confirmed"
            session.save()
            return JsonResponse(session_serializer(session), status=200)
        else:
            return JsonResponse({"error": "Invalid OTP code"}, status=400)

    except Session.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
