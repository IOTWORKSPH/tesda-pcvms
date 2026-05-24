# config/settings/local.py

from .base import *

DEBUG = True

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost"]
)

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]
)

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# SQLite on Windows can intermittently fail while Django writes DB-backed
# sessions during local login. Keep development sessions in signed cookies so
# admin and app login do not depend on the sqlite session table.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend"
)

INTERNAL_IPS = [
    "127.0.0.1",
]
