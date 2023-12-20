from django.views import View
from django.http import JsonResponse
import json

from session_system.token_authentication_middleware import token_auth
from .models import User, Device, Session


# Create your views here.
# @token_auth


class SessionView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user_email = data.get("user", {}).get("email")
            device_type = data.get("device", {}).get("type")

            if not user_email or not device_type:
                return JsonResponse({"error": "Invalid data"}, status=400)
            user, user_created = User.objects.get_or_create(email=user_email)
            device, device_created = Device.objects.get_or_create(
                user=user, type=device_type
            )

            # Create a new Session
            session = Session.objects.create(
                user=user,
                device=device,
                is_new_user=user_created,
                is_new_device=device_created,
            )
            print(f"OTP CODE: {session.otp_code}")
            return JsonResponse(
                {
                    "uuid": str(session),
                    "token": session.token,
                    "status": session.status,
                    "user": {
                        "uuid": str(user),
                        "email": user.email,
                    },
                    "device": {
                        "uuid": str(device),
                        "type": device.type,
                    },
                },
                status=201,
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
