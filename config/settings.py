"""
Django settings for TESDA PCVMS (config project)
Government-Grade Financial System
"""

from pathlib import Path
from decouple import config

# -------------------------------------------------
# Base Directory
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------------------------
# SECURITY
# -------------------------------------------------
SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', cast=bool)  # Change to False in production

ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')  # Add domain in production


# -------------------------------------------------
# APPLICATIONS
# -------------------------------------------------
INSTALLED_APPS = [
    # Django Core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Project Apps
    "core",
    "users",
    "finance",
    "pettycash",
    "reports",
    "audit",
]

AUTH_USER_MODEL = "users.User"


# -------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # Custom Entity Isolation Middleware
    "core.middleware.EntityPermissionMiddleware",
]


# -------------------------------------------------
# URL & WSGI
# -------------------------------------------------
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


# -------------------------------------------------
# TEMPLATES
# -------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Global templates folder
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                "pettycash.context_processors.notifications_processor",
            ],
        },
    },
]


# -------------------------------------------------
# DATABASE
# -------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# -------------------------------------------------
# PASSWORD VALIDATION
# -------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# -------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------
LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Manila"

USE_I18N = True
USE_TZ = True


# -------------------------------------------------
# STATIC FILES
# -------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"


# -------------------------------------------------
# MEDIA FILES
# -------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# -------------------------------------------------
# AUTHENTICATION (Namespace Safe)
# -------------------------------------------------
LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "users:role_redirect"
LOGOUT_REDIRECT_URL = "users:login"


# -------------------------------------------------
# SESSION & SECURITY HARDENING
# -------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1800  # 30 minutes auto logout


# -------------------------------------------------
# DEFAULT AUTO FIELD
# -------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
