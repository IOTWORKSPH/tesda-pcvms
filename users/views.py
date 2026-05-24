
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
    today = timezone.now().date()

    status_filter = request.GET.get("status")
    search_query = request.GET.get("q")

    # =====================================================
    # BASE QUERY (FOR TABLE DISPLAY)
    # =====================================================
    qs = PettyCashVoucher.objects.filter(
        requester=user,
        is_replenished=False
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
    base_qs = PettyCashVoucher.objects.filter(
        requester=user,
        is_replenished=False
    )

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

    awaiting_release_amount = base_qs.filter(
        transaction_type=TransactionType.CASH_ADVANCE,
        status=VoucherStatus.APPROVED,
    ).aggregate(total=Sum("amount_requested"))["total"] or Decimal("0.00")

    for_refund_amount = base_qs.filter(
        transaction_type=TransactionType.REIMBURSEMENT,
        status=VoucherStatus.APPROVED,
    ).aggregate(total=Sum("amount_requested"))["total"] or Decimal("0.00")

    active_count = base_qs.exclude(
        status__in=[VoucherStatus.POSTED, VoucherStatus.CANCELLED]
    ).count()

    completed_count = base_qs.filter(
        status=VoucherStatus.POSTED
    ).count()

    total_requested_amount = base_qs.aggregate(
        total=Sum("amount_requested")
    )["total"] or Decimal("0.00")

    unliquidated_amount = base_qs.filter(
        transaction_type=TransactionType.CASH_ADVANCE,
        status=VoucherStatus.RELEASED,
    ).aggregate(total=Sum("amount_requested"))["total"] or Decimal("0.00")

    recent_request_count = base_qs.filter(
        created_at__date__gte=today - timedelta(days=7)
    ).count()

    total_visible = base_qs.count()
    completion_percent = Decimal("0.00")
    if total_visible > 0:
        completion_percent = round(
            Decimal(completed_count) / Decimal(total_visible) * Decimal("100"),
            2,
        )

    next_action_pcvs = base_qs.filter(
        Q(status=VoucherStatus.DRAFT) |
        Q(transaction_type=TransactionType.CASH_ADVANCE, status=VoucherStatus.RELEASED) |
        Q(transaction_type=TransactionType.REIMBURSEMENT, status=VoucherStatus.APPROVED)
    ).select_related("fund", "expense_category", "supplier").order_by("-updated_at", "-created_at")[:5]

    watched_pcvs = base_qs.filter(
        Q(status=VoucherStatus.FOR_APPROVAL) |
        Q(transaction_type=TransactionType.CASH_ADVANCE, status=VoucherStatus.APPROVED) |
        Q(transaction_type=TransactionType.CASH_ADVANCE, status=VoucherStatus.LIQUIDATED)
    ).select_related("fund", "expense_category", "supplier").order_by("-updated_at", "-created_at")[:5]

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
        "awaiting_release_amount": awaiting_release_amount,
        "for_refund_amount": for_refund_amount,
        "active_count": active_count,
        "completed_count": completed_count,
        "total_requested_amount": total_requested_amount,
        "unliquidated_amount": unliquidated_amount,
        "recent_request_count": recent_request_count,
        "completion_percent": completion_percent,
        "recent_pcvs": qs[:20],
        "next_action_pcvs": next_action_pcvs,
        "watched_pcvs": watched_pcvs,
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
    type_filter = request.GET.get("type")
    search_query = request.GET.get("q", "")
    today = timezone.now().date()

    # Base Query (Exclude Draft)
    voucher_scope = PettyCashVoucher.objects.filter(
        entity=entity
    ).exclude(
        status=VoucherStatus.DRAFT
    ).select_related(
        "requester", "fund", "expense_category", "supplier"
    ).order_by("-created_at")

    vouchers = voucher_scope

    if status_filter:
        vouchers = vouchers.filter(status=status_filter)

    if type_filter:
        vouchers = vouchers.filter(transaction_type=type_filter)

    if search_query:
        vouchers = vouchers.filter(
            Q(pcv_no__icontains=search_query) |
            Q(purpose__icontains=search_query) |
            Q(requester__first_name__icontains=search_query) |
            Q(requester__last_name__icontains=search_query) |
            Q(expense_category__name__icontains=search_query)
        )

    vouchers = list(vouchers[:50])  # limit for performance

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
    funds = PettyCashFund.objects.filter(entity=entity).select_related(
        "custodian",
        "fund_cluster",
        "responsibility_center",
    )

    total_fund_amount = funds.aggregate(
        total=Sum("fund_amount")
    )["total"] or Decimal("0.00")

    total_current_balance = funds.aggregate(
        total=Sum("current_balance")
    )["total"] or Decimal("0.00")

    utilization_percent = Decimal("0.00")

    if total_fund_amount > 0:
        utilization_percent = (
            (total_fund_amount - total_current_balance)
            / total_fund_amount
        ) * Decimal("100")

    total_utilized_amount = total_fund_amount - total_current_balance

    vouchers_this_week = PettyCashVoucher.objects.filter(
        entity=entity,
        created_at__date__gte=today - timedelta(days=7)
    ).exclude(status=VoucherStatus.DRAFT).count()

    approval_amount = PettyCashVoucher.objects.filter(
        entity=entity,
        status=VoucherStatus.FOR_APPROVAL
    ).aggregate(total=Sum("amount_requested"))["total"] or Decimal("0.00")

    released_amount = PettyCashVoucher.objects.filter(
        entity=entity,
        status=VoucherStatus.RELEASED,
        transaction_type=TransactionType.CASH_ADVANCE
    ).aggregate(total=Sum("amount_requested"))["total"] or Decimal("0.00")

    reimbursement_ready = PettyCashVoucher.objects.filter(
        entity=entity,
        status=VoucherStatus.APPROVED,
        transaction_type=TransactionType.REIMBURSEMENT
    ).count()

    reimbursement_ready_amount = PettyCashVoucher.objects.filter(
        entity=entity,
        status=VoucherStatus.APPROVED,
        transaction_type=TransactionType.REIMBURSEMENT
    ).aggregate(total=Sum("amount_requested"))["total"] or Decimal("0.00")

    posted_this_month = voucher_scope.filter(
        status=VoucherStatus.POSTED,
        created_at__year=today.year,
        created_at__month=today.month,
    ).aggregate(total=Sum("amount_requested"))["total"] or Decimal("0.00")

    approval_qs = PettyCashVoucher.objects.filter(
        entity=entity,
        status=VoucherStatus.FOR_APPROVAL
    ).select_related("requester", "fund", "expense_category")

    ready_for_approval = 0
    fund_exception_count = 0
    approval_aging_count = 0
    for approval in approval_qs:
        if approval.amount_requested <= approval.fund.current_balance:
            ready_for_approval += 1
        else:
            fund_exception_count += 1

        if (today - approval.created_at.date()).days >= 3:
            approval_aging_count += 1

    unliquidated_qs = PettyCashVoucher.objects.filter(
        entity=entity,
        status=VoucherStatus.RELEASED,
        transaction_type=TransactionType.CASH_ADVANCE
    ).select_related("requester", "fund")

    liquidation_at_risk = 0
    liquidation_overdue = 0
    liquidation_aging_items = []
    for released in unliquidated_qs:
        days_open = 0
        if released.release_date:
            days_open = (today - released.release_date.date()).days

        if days_open >= 15:
            liquidation_overdue += 1
            risk = "danger"
        elif days_open >= 7:
            liquidation_at_risk += 1
            risk = "warning"
        else:
            risk = "normal"

        released.days_open = days_open
        released.risk = risk
        liquidation_aging_items.append(released)

    fund_cards = []
    for fund in funds:
        used = fund.fund_amount - fund.current_balance
        fund_utilization = Decimal("0.00")
        if fund.fund_amount > 0:
            fund_utilization = round((used / fund.fund_amount) * Decimal("100"), 2)

        fund.utilized_amount = used
        fund.utilization_percent = fund_utilization
        fund.health = (
            "danger" if fund_utilization >= 75
            else "warning" if fund_utilization >= 50
            else "healthy"
        )
        fund_cards.append(fund)

    category_spend = voucher_scope.values(
        "expense_category__name"
    ).annotate(
        total=Sum("amount_requested"),
        count=Count("id"),
    ).order_by("-total")[:5]

    requester_activity = voucher_scope.values(
        "requester__first_name",
        "requester__last_name",
    ).annotate(
        total=Sum("amount_requested"),
        count=Count("id"),
    ).order_by("-count", "-total")[:5]

    # Approval Aging
    for voucher in vouchers:
        if voucher.status == VoucherStatus.FOR_APPROVAL:
            voucher.days_pending = (
                today - voucher.created_at.date()
            ).days
        else:
            voucher.days_pending = None

        voucher.has_fund_exception = (
            voucher.status == VoucherStatus.FOR_APPROVAL and
            voucher.amount_requested > voucher.fund.current_balance
        )

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
        "total_utilized_amount": total_utilized_amount,
        "utilization_percent": round(utilization_percent, 2),
        "vouchers_this_week": vouchers_this_week,
        "approval_amount": approval_amount,
        "released_amount": released_amount,
        "reimbursement_ready": reimbursement_ready,
        "reimbursement_ready_amount": reimbursement_ready_amount,
        "posted_this_month": posted_this_month,
        "ready_for_approval": ready_for_approval,
        "fund_exception_count": fund_exception_count,
        "approval_aging_count": approval_aging_count,
        "liquidation_at_risk": liquidation_at_risk,
        "liquidation_overdue": liquidation_overdue,
        "liquidation_aging_items": liquidation_aging_items[:5],
        "fund_cards": fund_cards,
        "category_spend": category_spend,
        "requester_activity": requester_activity,
        "recent_logs": recent_logs,
        "active_status": status_filter,
        "active_type": type_filter,
        "search_query": search_query,
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
    current_balance = (
        fund.current_balance
        if fund.current_balance is not None
        else Decimal("0.00")
    )
    utilized_amount = total_fund - current_balance

    utilization_percent = Decimal("0.00")
    if total_fund > 0:
        utilization_percent = round((utilized_amount / total_fund) * 100, 2)

    available_percent = Decimal("0.00")
    if total_fund > 0:
        available_percent = round((current_balance / total_fund) * 100, 2)

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

    # Cash advances already released but not yet liquidated
    unliquidated_amount = PettyCashVoucher.objects.filter(
        fund=fund,
        status=VoucherStatus.RELEASED,
        transaction_type=TransactionType.CASH_ADVANCE
    ).aggregate(total=Sum("amount_requested"))["total"] or Decimal("0.00")

    # Cash advances already liquidated but adjustment not yet finalized
    pending_finalization_amount = PettyCashVoucher.objects.filter(
        fund=fund,
        status=VoucherStatus.LIQUIDATED,
        transaction_type=TransactionType.CASH_ADVANCE,
        is_posted_to_ledger=False
    ).aggregate(total=Sum("amount_requested"))["total"] or Decimal("0.00")

    # Current posted exposure that is already deducted from fund
    # and not part of unliquidated / pending-finalization cash advances
    reimbursed_amount = utilized_amount - unliquidated_amount - pending_finalization_amount

    if reimbursed_amount < 0:
        reimbursed_amount = Decimal("0.00")

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

    today = timezone.now().date()
    aging_items = []
    overdue_liquidation_count = 0
    for voucher in unliquidated_cash_advances:
        if voucher.release_date:
            days_open = (today - voucher.release_date.date()).days
        else:
            days_open = 0

        if days_open >= 15:
            risk = "danger"
            overdue_liquidation_count += 1
        elif days_open >= 7:
            risk = "warning"
        else:
            risk = "normal"

        voucher.days_open = days_open
        voucher.risk = risk
        aging_items.append(voucher)

    ledger_snapshot = LedgerEntry.objects.filter(
        fund=fund
    ).order_by("-transaction_date", "-id")[:10]

    context = {
        "fund": fund,
        "total_fund": total_fund,
        "current_balance": current_balance,
        "utilized_amount": utilized_amount,
        "utilization_percent": utilization_percent,
        "available_percent": available_percent,
        "show_replenishment_alert": show_replenishment_alert,
        "active_replenishment_exists": active_replenishment_exists,

        "unliquidated_amount": unliquidated_amount,
        "pending_finalization_amount": pending_finalization_amount,
        "reimbursed_amount": reimbursed_amount,

        "for_release": for_release,
        "for_reimbursement": for_reimbursement,
        "for_liquidation": for_liquidation,
        "unliquidated_cash_advances": unliquidated_cash_advances,
        "aging_items": aging_items[:8],
        "overdue_liquidation_count": overdue_liquidation_count,
        "for_release_count": for_release.count(),
        "for_reimbursement_count": for_reimbursement.count(),
        "for_liquidation_count": for_liquidation.count(),
        "unliquidated_count": unliquidated_cash_advances.count(),
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

    total_pending_amount = pending_inspection.aggregate(
        total=Sum("amount_liquidated")
    )["total"] or Decimal("0.00")

    ready_today = pending_inspection.filter(
        purchase_date=timezone.now().date()
    ).count()

    overdue_rate = Decimal("0.00")
    if total_pending > 0:
        overdue_rate = round(
            Decimal(overdue) / Decimal(total_pending) * Decimal("100"),
            2,
        )

    context = {
        "total_pending": total_pending,
        "overdue": overdue,
        "ready_today": ready_today,
        "total_pending_amount": total_pending_amount,
        "overdue_rate": overdue_rate,
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

    pending_amount = pending_iar.aggregate(
        total=Sum("amount_requested")
    )["total"] or Decimal("0.00")

    issued_amount = issued_this_month.aggregate(
        total=Sum("amount_requested")
    )["total"] or Decimal("0.00")

    processed_vouchers = PettyCashVoucher.objects.filter(
        entity=entity,
        iar_no__isnull=False
    ).count()

    iar_completion_rate = Decimal("0.00")
    total_supply_scope = pending_count + processed_vouchers
    if total_supply_scope > 0:
        iar_completion_rate = round(
            Decimal(processed_vouchers) / Decimal(total_supply_scope) * Decimal("100"),
            2,
        )

    context = {
        "pending_count": pending_count,
        "issued_count": issued_count,
        "total_items": total_items,
        "pending_amount": pending_amount,
        "issued_amount": issued_amount,
        "processed_vouchers": processed_vouchers,
        "iar_completion_rate": iar_completion_rate,
        "recent_iars": recent_iars,
    }

    return render(request, "users/dashboard_supply.html", context)


