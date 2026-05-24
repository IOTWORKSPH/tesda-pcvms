# config/settings/base.py

from pathlib import Path
import environ
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    environ.Env.read_env(str(ENV_FILE))


# =========================================================
# CORE
# =========================================================
SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me")
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

LANGUAGE_CODE = env("LANGUAGE_CODE", default="en-us")
TIME_ZONE = env("TIME_ZONE", default="Asia/Manila")
USE_I18N = True
USE_TZ = env.bool("USE_TZ", default=True)


# =========================================================
# APPLICATIONS
# =========================================================
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "unfold",
]

LOCAL_APPS = [
    "audit",
    "core",
    "finance",
    "pettycash",
    "reports",
    "users",
]

INSTALLED_APPS = THIRD_PARTY_APPS + DJANGO_APPS + LOCAL_APPS


# =========================================================
# DJANGO UNFOLD ADMIN THEME
# =========================================================
UNFOLD = {
    "SITE_TITLE": "TESDA PCVMS Admin",
    "SITE_HEADER": "TESDA PCVMS",
    "SITE_SUBHEADER": "Petty Cash Voucher Management System",
    "SITE_URL": "/",
    "SITE_SYMBOL": "account_balance_wallet",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "BORDER_RADIUS": "6px",
    "COLORS": {
        "primary": {
            "50": "oklch(97.7% .018 232.2)",
            "100": "oklch(94.8% .041 232.7)",
            "200": "oklch(89.6% .078 230.1)",
            "300": "oklch(81.7% .122 226.8)",
            "400": "oklch(71.8% .156 224.2)",
            "500": "oklch(62.8% .176 225.1)",
            "600": "oklch(53.7% .173 230.5)",
            "700": "oklch(45.9% .145 234.3)",
            "800": "oklch(38.5% .113 237.8)",
            "900": "oklch(32.9% .084 240.2)",
            "950": "oklch(23.8% .062 244.4)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("People"),
                "separator": False,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "people",
                        "link": reverse_lazy("admin:users_user_changelist"),
                    },
                    {
                        "title": _("Groups & Roles"),
                        "icon": "admin_panel_settings",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                    {
                        "title": _("Entities"),
                        "icon": "corporate_fare",
                        "link": reverse_lazy("admin:users_entity_changelist"),
                    },
                ],
            },
            {
                "title": _("Petty Cash Operations"),
                "separator": True,
                "items": [
                    {
                        "title": _("Petty Cash Vouchers"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:pettycash_pettycashvoucher_changelist"),
                    },
                    {
                        "title": _("Expense Categories"),
                        "icon": "category",
                        "link": reverse_lazy("admin:pettycash_expensecategory_changelist"),
                    },
                    {
                        "title": _("Suppliers"),
                        "icon": "storefront",
                        "link": reverse_lazy("admin:pettycash_supplier_changelist"),
                    },
                ],
            },
            {
                "title": _("Finance Setup"),
                "separator": True,
                "items": [
                    {
                        "title": _("Petty Cash Funds"),
                        "icon": "account_balance_wallet",
                        "link": reverse_lazy("admin:finance_pettycashfund_changelist"),
                    },
                    {
                        "title": _("Fund Clusters"),
                        "icon": "account_tree",
                        "link": reverse_lazy("admin:finance_fundcluster_changelist"),
                    },
                    {
                        "title": _("Responsibility Centers"),
                        "icon": "business",
                        "link": reverse_lazy("admin:finance_responsibilitycenter_changelist"),
                    },
                    {
                        "title": _("Ledger Entries"),
                        "icon": "menu_book",
                        "link": reverse_lazy("admin:finance_ledgerentry_changelist"),
                    },
                ],
            },
            {
                "title": _("Audit"),
                "separator": True,
                "items": [
                    {
                        "title": _("Audit Logs"),
                        "icon": "history",
                        "link": reverse_lazy("admin:audit_auditlog_changelist"),
                    },
                ],
            },
        ],
    },
}


# =========================================================
# MIDDLEWARE
# =========================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.FrontendSecurityHeadersMiddleware",
    "core.middleware.EntityPermissionMiddleware",
]


# =========================================================
# URLS / WSGI / ASGI
# =========================================================
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# =========================================================
# TEMPLATES
# =========================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "pettycash.context_processors.notifications_processor",
            ],
        },
    },
]


# =========================================================
# DATABASE
# =========================================================
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}"
    )
}

DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)

if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"]["CONN_MAX_AGE"] = 0
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"].setdefault("timeout", 20)

if DATABASES["default"]["ENGINE"] == "django.db.backends.mysql":
    DATABASES["default"]["OPTIONS"] = {
        "charset": "utf8mb4",
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
    }


# =========================================================
# PASSWORD VALIDATION
# =========================================================
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


# =========================================================
# CUSTOM USER / AUTH
# =========================================================
AUTH_USER_MODEL = "users.User"
LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "users:role_redirect"
LOGOUT_REDIRECT_URL = "users:login"


# =========================================================
# STATIC / MEDIA
# =========================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = []
if (BASE_DIR / "static").exists():
    STATICFILES_DIRS.append(BASE_DIR / "static")

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =========================================================
# EMAIL
# =========================================================
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="TESDA PCVMS <no-reply@localhost>"
)
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)


# =========================================================
# WEASYPRINT / PDF
# =========================================================
WEASYPRINT_ENABLED = env.bool("WEASYPRINT_ENABLED", default=False)


# =========================================================
# SECURITY DEFAULTS
# =========================================================
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=not DEBUG)

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=False,
)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)


# =========================================================
# DEFAULT PK
# =========================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =========================================================
# LOGGING
# =========================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("LOG_LEVEL", default="INFO"),
    },
}
