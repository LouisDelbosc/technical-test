from django.http import JsonResponse
from django.urls import resolve
from .models import Session
import logging


def token_auth(view_func):
    view_func.token_auth = True
    return view_func


logger = logging.getLogger(__name__)

class TokenAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the view is marked to bypass token authentication
        view = resolve(request.path_info).func
        if not getattr(view, "token_auth", False):
            return self.get_response(request)

        authorization_header = request.headers.get("Authorization")
        if authorization_header:
            # Split the header to extract the token
            parts = authorization_header.split()
            if len(parts) == 2 and parts[0] == "Bearer":
                token = parts[1]
                session = Session.objects.filter(token=token).first()
                if session and session.user:
                    request.session = session
                    return self.get_response(request)
        return JsonResponse({"error": "Unauthorized"}, status=401)
