#Core/middleware.py codes
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseForbidden


class EntityPermissionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        path = request.path

        # Allow admin, login, static, media
        if (
            path.startswith("/admin")
            or path.startswith("/static")
            or path.startswith("/media")
            or path == reverse("users:login")
        ):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect("users:login")

        # Superuser bypass
        if request.user.is_superuser:
            return self.get_response(request)

        # System admin bypass
        if request.user.is_system_admin:
            request.current_entity = request.user.entity
            return self.get_response(request)

        if not request.user.entity:
            return HttpResponseForbidden(
                "Access Denied: No assigned entity."
            )

        request.current_entity = request.user.entity

        return self.get_response(request)
