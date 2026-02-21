from django.contrib import admin
from .models import (
    FundCluster,
    ResponsibilityCenter,
    PettyCashFund,
    LedgerEntry
)


# ==========================================================
# FUND CLUSTER ADMIN
# ==========================================================

@admin.register(FundCluster)
class FundClusterAdmin(admin.ModelAdmin):

    list_display = ("code", "description")
    search_fields = ("code", "description")
    ordering = ("code",)


# ==========================================================
# RESPONSIBILITY CENTER ADMIN
# ==========================================================

@admin.register(ResponsibilityCenter)
class ResponsibilityCenterAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "description",
        "entity",
        "fund_cluster",
        "is_active",
    )

    list_filter = (
        "entity",
        "fund_cluster",
        "is_active",
    )

    search_fields = (
        "code",
        "description",
    )

    ordering = ("code",)


# ==========================================================
# PETTY CASH FUND ADMIN
# ==========================================================

@admin.register(PettyCashFund)
class PettyCashFundAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "entity",
        "fund_cluster",
        "responsibility_center",
        "custodian",
        "fund_amount",
        "current_balance",
        "is_active",
    )

    list_filter = (
        "entity",
        "fund_cluster",
        "is_active",
    )

    search_fields = (
        "name",
        "entity__name",
        "custodian__username",
    )

    ordering = ("entity", "name")


# ==========================================================
# LEDGER ENTRY ADMIN (READ ONLY)
# ==========================================================

@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):

    list_display = (
        "transaction_date",
        "fund",
        "reference_type",
        "reference_no",
        "debit",
        "credit",
        "running_balance",
        "is_reversal",
    )

    list_filter = (
        "fund",
        "reference_type",
        "transaction_date",
    )

    search_fields = (
        "reference_no",
        "description",
    )

    ordering = ("-transaction_date", "-id")

    readonly_fields = (
        "fund",
        "transaction_date",
        "debit",
        "credit",
        "running_balance",
        "reference_type",
        "reference_no",
        "description",
        "created_by",
        "is_reversal",
        "reversed_entry",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
