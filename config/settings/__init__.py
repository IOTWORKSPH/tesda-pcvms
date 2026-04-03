# config/settings/__init__.py

import os
from django.core.exceptions import ImproperlyConfigured
from .base import *

DJANGO_ENV = os.getenv("DJANGO_ENV", "local").lower()

if DJANGO_ENV == "local":
    from .local import *
elif DJANGO_ENV == "production":
    from .production import *
else:
    raise ImproperlyConfigured(
        "DJANGO_ENV must be either 'local' or 'production'."
    )