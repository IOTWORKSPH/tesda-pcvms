#decorators.py
from django.core.exceptions import PermissionDenied
from functools import wraps


def role_required(*roles):
    """
    Restrict access based on Django Group roles.
    Supports multiple roles.
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            user = request.user

            if not user.is_authenticated:
                raise PermissionDenied

            # Superuser bypass
            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Check roles
            if any(user.has_role(role) for role in roles):
                return view_func(request, *args, **kwargs)

            raise PermissionDenied

        return wrapper

    return decorator
