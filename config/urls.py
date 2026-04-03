# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from users.views import login_view


urlpatterns = [

    # =========================================
    # ADMIN
    # =========================================
    path("admin/", admin.site.urls),

    # =========================================
    # ROOT
    # =========================================
    path("", login_view, name="root-login"),

    # =========================================
    # APP URLS
    # =========================================
    path("users/", include("users.urls", namespace="users")),
    path("pettycash/", include("pettycash.urls", namespace="pettycash")),

    # =========================================
    # PASSWORD SET (Used by EmailService)
    # =========================================
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_set.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_set_complete.html"
        ),
        name="password_reset_complete",
    ),
]


# =========================================
# MEDIA FILES (DEV ONLY)
# =========================================
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )


# =========================================
# CUSTOM ERROR HANDLER
# =========================================
handler403 = "core.views.custom_403"