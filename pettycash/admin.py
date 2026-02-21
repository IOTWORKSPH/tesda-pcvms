from django.contrib import admin
from django.db.models import Sum
from .models import (
    Supplier,
    ExpenseCategory,
    PettyCashVoucher,
    PCVItem,
    ReceiptAttachment,
    PCVApproval
)


# ==========================================================
# SUPPLIER ADMIN
# ==========================================================

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):

    list_display = ("name", "entity", "tin", "is_active")
    list_filter = ("entity", "is_active")
    search_fields = ("name", "tin")
    ordering = ("name",)


# ==========================================================
# EXPENSE CATEGORY ADMIN
# ==========================================================

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):

    list_display = ("code", "name", "entity", "is_active")
    list_filter = ("entity", "is_active")
    search_fields = ("code", "name")
    ordering = ("code",)


# ==========================================================
# INLINE MODELS
# ==========================================================

class PCVItemInline(admin.TabularInline):
    model = PCVItem
    extra = 1


class ReceiptAttachmentInline(admin.TabularInline):
    model = ReceiptAttachment
    extra = 0


class PCVApprovalInline(admin.TabularInline):
    model = PCVApproval
    extra = 0
    readonly_fields = ("approved_by", "role", "remarks", "created_at")


# ==========================================================
# PETTY CASH VOUCHER ADMIN
# ==========================================================

@admin.register(PettyCashVoucher)
class PettyCashVoucherAdmin(admin.ModelAdmin):

    list_display = (
        "pcv_no",
        "entity",
        "transaction_type",
        "requester",
        "amount_requested",
        "amount_liquidated",
        "status",
        "is_posted_to_ledger",
    )

    list_filter = (
        "entity",
        "transaction_type",
        "status",
        "is_posted_to_ledger",
    )

    search_fields = (
        "pcv_no",
        "official_receipt_number",
        "requester__username",
    )

    ordering = ("-created_at",)

    inlines = [
        PCVItemInline,
        ReceiptAttachmentInline,
        PCVApprovalInline,
    ]

    readonly_fields = (
        "amount_liquidated",
        "is_posted_to_ledger",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "entity",
                "fund",
                "pcv_no",
                "transaction_type",
                "status",
            )
        }),

        ("Request Details", {
            "fields": (
                "requester",
                "purpose",
                "expense_category",
                "amount_requested",
            )
        }),

        ("Reimbursement Details", {
            "fields": (
                "purchase_date",
                "supplier",
                "official_receipt_number",
            )
        }),

        ("System Tracking", {
            "fields": (
                "amount_liquidated",
                "is_posted_to_ledger",
                "created_at",
                "updated_at",
            )
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion once voucher exists
        return False
