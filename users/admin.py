from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Entity


# ==========================================================
# ENTITY ADMIN
# ==========================================================

@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    """
    Government Entity Configuration
    """

    list_display = (
        "code",
        "name",
        "tin",
        "is_active",
    )

    search_fields = (
        "code",
        "name",
        "tin",
    )

    list_filter = (
        "is_active",
    )

    ordering = ("name",)


# ==========================================================
# CUSTOM USER ADMIN
# ==========================================================

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    Enterprise-Grade Custom User Administration
    Designed for Government Financial Systems
    """

    # =============================
    # LIST DISPLAY
    # =============================

    list_display = (
        "username",
        "employee_number",
        "get_full_name",
        "entity",
        "position",
        "designation",
        "office",
        "is_system_admin",
        "is_active_employee",
        "is_staff",
    )

    list_filter = (
        "entity",
        "is_system_admin",
        "is_active_employee",
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
    )

    search_fields = (
        "username",
        "employee_number",
        "first_name",
        "last_name",
        "office",
        "designation",
    )

    ordering = ("employee_number",)

    # =============================
    # FIELD ORGANIZATION
    # =============================

    fieldsets = (
        ("Authentication", {
            "fields": ("username", "password")
        }),

        ("Personal Information", {
            "fields": (
                "first_name",
                "last_name",
                "email",
                "employee_number",
            )
        }),

        ("Government Assignment", {
            "fields": (
                "entity",
                "position",
                "designation",
                "office",
            )
        }),

        ("System Roles & Access", {
            "fields": (
                "groups",
                "is_system_admin",
                "is_staff",
                "is_superuser",
                "is_active",
                "is_active_employee",
            )
        }),

        ("Digital Assets", {
            "fields": (
                "profile_image",
                "signature",
            )
        }),

        ("Important Dates", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    # =============================
    # ADD USER FORM
    # =============================

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "employee_number",
                    "first_name",
                    "last_name",
                    "email",
                    "entity",
                    "position",
                    "designation",
                    "office",
                    "groups",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    # =============================
    # READ ONLY FIELDS
    # =============================

    readonly_fields = (
        "last_login",
        "date_joined",
    )
