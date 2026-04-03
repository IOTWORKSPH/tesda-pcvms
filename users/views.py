
#Users Views.py Codes
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Count, Q, Sum
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from pettycash.models import (
    PettyCashVoucher,
    VoucherStatus,
    TransactionType,
    PCVItem,
    Replenishment,
    ReplenishmentStatus,
)

from finance.models import PettyCashFund, LedgerEntry
from audit.models import AuditLog
from pettycash.services.dashboard_service import CustodianDashboardService


def user_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


def login_view(request):

    # 🔥 If already authenticated, clear old messages first
    if request.user.is_authenticated:
        storage = messages.get_messages(request)
        for _ in storage:
            pass  # clear message storage

        return redirect("users:role_redirect")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Clear any old login errors before redirect
            storage = messages.get_messages(request)
            for _ in storage:
                pass

            if user.is_superuser:
                return redirect("/admin/")

            return redirect("users:role_redirect")

        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "users/login.html")

    return render(request, "users/login.html")


@login_required
def logout_view(request):
    logout(request)

    # 🔥 CLEAR MESSAGE STORAGE
    storage = messages.get_messages(request)
    list(storage)  # Force evaluation → clears them

    return redirect("users:login")


ROLE_PRIORITY = [
    "Administrator",
    "Custodian",
    "Inspection",
    "Supply",
    "Staff",
]

@login_required
def role_redirect(request):
    user = request.user

    if user.is_superuser:
        return redirect("/admin/")

    for role in ROLE_PRIORITY:
        if user.has_role(role):
            return redirect(f"users:dashboard_{role.lower()}")

    return render(request, "403.html", status=403)


@login_required
def dashboard_staff(request):

    user = request.user

    status_filter = request.GET.get("status")
    search_query = request.GET.get("q")

    # =====================================================
    # BASE QUERY (FOR TABLE DISPLAY)
    # =====================================================
    qs = PettyCashVoucher.objects.filter(
        requester=user
    ).select_related(
        "fund",
        "expense_category",
        "supplier"
    ).order_by("-created_at")

    # =====================================================
    # KPI FILTERING (TABLE FILTER ONLY)
    # =====================================================
    if status_filter:

        if status_filter == "UNLIQUIDATED":
            qs = qs.filter(
                transaction_type="CASH_ADVANCE",
                status=VoucherStatus.RELEASED
            )

        elif status_filter == "FOR_REFUND":
            qs = qs.filter(
                transaction_type="REIMBURSEMENT",
                status=VoucherStatus.APPROVED
            )

        elif status_filter == "APPROVED":
            qs = qs.filter(
                transaction_type="CASH_ADVANCE",
                status=VoucherStatus.APPROVED
            )

        else:
            qs = qs.filter(status=status_filter)

    # =====================================================
    # SEARCH FILTER
    # =====================================================
    if search_query:
        qs = qs.filter(
            Q(pcv_no__icontains=search_query) |
            Q(purpose__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )

    # =====================================================
    # KPI COUNTS (ALWAYS FULL DATA — NOT FILTERED)
    # =====================================================
    base_qs = PettyCashVoucher.objects.filter(requester=user)

    draft_count = base_qs.filter(
        status=VoucherStatus.DRAFT
    ).count()

    for_approval_count = base_qs.filter(
        status=VoucherStatus.FOR_APPROVAL
    ).count()

    # Approved = Cash Advance Approved (Awaiting Release)
    approved_count = base_qs.filter(
        transaction_type="CASH_ADVANCE",
        status=VoucherStatus.APPROVED
    ).count()

    # For Refund = Reimbursement Approved by Admin
    for_refund_count = base_qs.filter(
        transaction_type="REIMBURSEMENT",
        status=VoucherStatus.APPROVED
    ).count()

    # Refunded = Completed Reimbursement
    refunded_count = base_qs.filter(
        transaction_type="REIMBURSEMENT",
        status=VoucherStatus.LIQUIDATED
    ).count()

    # Unliquidated = Cash Advance Released
    settlement_count = base_qs.filter(
        transaction_type="CASH_ADVANCE",
        status=VoucherStatus.RELEASED
    ).count()

    # =====================================================
    # CONTEXT
    # =====================================================
    context = {
        "draft_count": draft_count,
        "for_approval_count": for_approval_count,
        "approved_count": approved_count,
        "for_refund_count": for_refund_count,
        "refunded_count": refunded_count,
        "settlement_count": settlement_count,
        "recent_pcvs": qs[:20],
        "active_status": status_filter,
        "search_query": search_query,
    }

    return render(
        request,
        "users/dashboard_staff.html",
        context
    )



@login_required
def dashboard_administrator(request):

    if not request.user.has_role("Administrator"):
        return render(request, "403.html", status=403)

    entity = request.user.entity
    status_filter = request.GET.get("status")

    # Base Query (Exclude Draft)
    vouchers = PettyCashVoucher.objects.filter(
        entity=entity
    ).exclude(
        status=VoucherStatus.DRAFT
    ).select_related(
        "requester", "fund"
    ).order_by("-created_at")

    if status_filter:
        vouchers = vouchers.filter(status=status_filter)

    vouchers = vouchers[:50]  # limit for performance

    # =========================
    # KPI COUNTS (Corrected)
    # =========================

    for_approval = PettyCashVoucher.objects.filter(
        entity=entity,
        status=VoucherStatus.FOR_APPROVAL
    ).count()

    # Only Cash Advance needs release
    awaiting_release = PettyCashVoucher.objects.filter(
        entity=entity,
        status=VoucherStatus.APPROVED,
        transaction_type=TransactionType.CASH_ADVANCE
    ).count()

    # All released cash advances (unliquidated)
    unliquidated = PettyCashVoucher.objects.filter(
        entity=entity,
        status=VoucherStatus.RELEASED,
        transaction_type=TransactionType.CASH_ADVANCE
    ).count()

    # Liquidated but not yet finalized
    pending_finalization = PettyCashVoucher.objects.filter(
        entity=entity,
        status=VoucherStatus.LIQUIDATED,
        transaction_type=TransactionType.CASH_ADVANCE,
        is_posted_to_ledger=False
    ).count()

    # Fund Summary
    funds = PettyCashFund.objects.filter(entity=entity)

    total_fund_amount = funds.aggregate(
        total=Sum("fund_amount")
    )["total"] or Decimal("0.00")

    total_current_balance = funds.aggregate(
        total=Sum("current_balance")
    )["total"] or Decimal("0.00")

    total_current_balance = funds.aggregate(
        total=Sum("current_balance")
    )["total"] or 0

    utilization_percent = Decimal("0.00")

    if total_fund_amount > 0:
        utilization_percent = (
            (total_fund_amount - total_current_balance)
            / total_fund_amount
        ) * Decimal("100")

    # Approval Aging
    for voucher in vouchers:
        if voucher.status == VoucherStatus.FOR_APPROVAL:
            voucher.days_pending = (
                timezone.now().date() - voucher.created_at.date()
            ).days
        else:
            voucher.days_pending = None

    # Recent Logs
    recent_logs = AuditLog.objects.filter(
        entity=entity
    ).select_related("user")[:10]

    context = {
        "vouchers": vouchers,
        "for_approval": for_approval,
        "awaiting_release": awaiting_release,
        "overdue_liquidation": unliquidated,
        "unposted": pending_finalization,
        "total_fund_amount": total_fund_amount,
        "total_current_balance": total_current_balance,
        "utilization_percent": round(utilization_percent, 2),
        "recent_logs": recent_logs,
        "active_status": status_filter,
    }

    return render(
        request,
        "users/dashboard_administrator.html",
        context
    )




@login_required
def dashboard_custodian(request):

    if not request.user.has_role("Custodian"):
        return render(request, "403.html", status=403)

    fund = PettyCashFund.objects.filter(
        custodian=request.user,
        is_active=True
    ).first()

    if not fund:
        return render(request, "pettycash/no_fund.html")

    # =====================================================
    # FUND POSITION
    # =====================================================

    total_fund = fund.fund_amount

    ledger_totals = LedgerEntry.objects.filter(
        fund=fund
    ).aggregate(
        total_debit=Sum("debit"),
        total_credit=Sum("credit"),
    )

    total_debit = ledger_totals["total_debit"] or Decimal("0.00")
    total_credit = ledger_totals["total_credit"] or Decimal("0.00")

    current_balance = total_debit - total_credit
    utilized_amount = total_fund - current_balance

    utilization_percent = Decimal("0.00")
    if total_fund > 0:
        utilization_percent = round((utilized_amount / total_fund) * 100, 2)

    # =====================================================
    # CHECK IF REPLENISHMENT IS ALREADY IN PROCESS
    # =====================================================

    active_replenishment_exists = Replenishment.objects.filter(
        fund=fund,
        status__in=[
            ReplenishmentStatus.DRAFT,
            ReplenishmentStatus.SUBMITTED_TO_ACCOUNTING,
        ]
    ).exists()

    show_replenishment_alert = (
        utilization_percent >= 75
        and not active_replenishment_exists
    )

    # =====================================================
    # FINANCIAL BREAKDOWN
    # =====================================================

    # Released cash advances still fully outstanding
    unliquidated_amount = PettyCashVoucher.objects.filter(
        fund=fund,
        status=VoucherStatus.RELEASED,
        transaction_type=TransactionType.CASH_ADVANCE
    ).aggregate(total=Sum("amount_requested"))["total"] or Decimal("0.00")

    # Liquidated but not yet finalized:
    # full amount is still outstanding until excess/shortage is posted
    pending_finalization_amount = PettyCashVoucher.objects.filter(
        fund=fund,
        status=VoucherStatus.LIQUIDATED,
        transaction_type=TransactionType.CASH_ADVANCE,
        is_posted_to_ledger=False
    ).aggregate(total=Sum("amount_requested"))["total"] or Decimal("0.00")

    # Posted unreplenished expenses = current utilized less the still-unfinalized exposures
    posted_unreplenished_amount = utilized_amount - unliquidated_amount - pending_finalization_amount

    # =====================================================
    # OPERATIONAL QUEUES
    # =====================================================

    for_release = PettyCashVoucher.objects.filter(
        fund=fund,
        status=VoucherStatus.APPROVED,
        transaction_type=TransactionType.CASH_ADVANCE
    ).select_related("requester")

    for_reimbursement = PettyCashVoucher.objects.filter(
        fund=fund,
        status=VoucherStatus.APPROVED,
        transaction_type=TransactionType.REIMBURSEMENT
    ).select_related("requester")

    for_liquidation = PettyCashVoucher.objects.filter(
        fund=fund,
        status=VoucherStatus.LIQUIDATED,
        transaction_type=TransactionType.CASH_ADVANCE,
        is_posted_to_ledger=False
    ).select_related("requester")

    unliquidated_cash_advances = PettyCashVoucher.objects.filter(
        fund=fund,
        status=VoucherStatus.RELEASED,
        transaction_type=TransactionType.CASH_ADVANCE
    ).select_related("requester")

    ledger_snapshot = LedgerEntry.objects.filter(
        fund=fund
    ).order_by("-id")[:10]

    context = {
        "fund": fund,
        "total_fund": total_fund,
        "current_balance": current_balance,
        "utilized_amount": utilized_amount,
        "utilization_percent": utilization_percent,
        "show_replenishment_alert": show_replenishment_alert,
        "active_replenishment_exists": active_replenishment_exists,

        "unliquidated_amount": unliquidated_amount,
        "pending_finalization_amount": pending_finalization_amount,
        "reimbursed_amount": posted_unreplenished_amount,

        "for_release": for_release,
        "for_reimbursement": for_reimbursement,
        "for_liquidation": for_liquidation,
        "unliquidated_cash_advances": unliquidated_cash_advances,
        "ledger_snapshot": ledger_snapshot,
    }

    return render(
        request,
        "users/dashboard_custodian.html",
        context
    )


@login_required
def dashboard_inspection(request):

    if not request.user.has_role("Inspection"):
        return render(request, "403.html", status=403)

    from pettycash.models import PettyCashVoucher, VoucherStatus
    from django.utils import timezone
    from datetime import timedelta

    entity = request.user.entity

    # ==========================================
    # VOUCHERS PENDING INSPECTION
    # ==========================================
    pending_inspection = PettyCashVoucher.objects.filter(
        entity=entity,
        status=VoucherStatus.LIQUIDATED
    ).select_related(
        "requester",
        "supplier",
        "fund"
    ).order_by("-purchase_date")

    # ==========================================
    # KPI COUNTS
    # ==========================================
    total_pending = pending_inspection.count()

    overdue = pending_inspection.filter(
        purchase_date__lt=timezone.now().date() - timedelta(days=7)
    ).count()

    # Recently liquidated
    recent = pending_inspection[:5]

    context = {
        "total_pending": total_pending,
        "overdue": overdue,
        "pending_inspection": pending_inspection,
        "recent": recent,
    }

    return render(request, "users/dashboard_inspection.html", context)


@login_required
def dashboard_supply(request):

    if not request.user.has_role("Supply"):
        return render(request, "403.html", status=403)

    entity = request.user.entity
    today = timezone.now()
    current_month = today.month
    current_year = today.year

    # Pending IAR
    pending_iar = PettyCashVoucher.objects.filter(
        entity=entity,
        status=VoucherStatus.APPROVED,
        iar_no__isnull=True
    )

    pending_count = pending_iar.count()

    # IAR Issued This Month
    issued_this_month = PettyCashVoucher.objects.filter(
        entity=entity,
        iar_no__isnull=False,
        created_at__year=current_year,
        created_at__month=current_month
    )

    issued_count = issued_this_month.count()

    # Total Items Processed
    total_items = PCVItem.objects.filter(
        voucher__entity=entity,
        voucher__iar_no__isnull=False
    ).count()

    # Recent IAR Records
    recent_iars = PettyCashVoucher.objects.filter(
        entity=entity,
        iar_no__isnull=False
    ).order_by("-created_at")[:10]

    context = {
        "pending_count": pending_count,
        "issued_count": issued_count,
        "total_items": total_items,
        "recent_iars": recent_iars,
    }

    return render(request, "users/dashboard_supply.html", context)


