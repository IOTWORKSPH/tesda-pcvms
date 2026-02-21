from django.contrib import admin
from .models import AuditLog



@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    # ======================================================
    # DISPLAY
    # ======================================================
    list_display = (
        "created_at",
        "entity",
        "user",
        "action",
        "model_name",
        "object_id",
        "previous_status",
        "new_status",
    )

    # ======================================================
    # FILTERING
    # ======================================================
    list_filter = (
        "entity",
        "action",
        "model_name",
        "created_at",
    )

    # ======================================================
    # SEARCH
    # ======================================================
    search_fields = (
        "object_id",
        "description",
        "user__username",
        "user__first_name",
        "user__last_name",
    )

    # ======================================================
    # READ ONLY (IMMUTABLE AUDIT)
    # ======================================================
    readonly_fields = (
        "entity",
        "user",
        "action",
        "model_name",
        "object_id",
        "description",
        "previous_status",
        "new_status",
        "created_at",
        "updated_at",
    )

    # ======================================================
    # PREVENT MANUAL CREATION
    # ======================================================
    def has_add_permission(self, request):
        return False

    # ======================================================
    # PREVENT DELETION
    # ======================================================
    def has_delete_permission(self, request, obj=None):
        return False

    # ======================================================
    # PREVENT EDITING
    # ======================================================
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True  # allow viewing list
        return False


