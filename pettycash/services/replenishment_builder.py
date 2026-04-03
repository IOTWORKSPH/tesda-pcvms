# pettycash/services/replenishment_builder.py

from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from collections import defaultdict

from finance.models import PettyCashFund
from pettycash.models import (
    PettyCashVoucher,
    ExpenseCategory,
    Replenishment,
    ReplenishmentStatus,
)


def _attach_report_display_numbers(vouchers):
    """
    Report-only numbering based on purchase date order.
    Does NOT overwrite official document numbers in the database.
    """
    counters = defaultdict(int)

    for voucher in vouchers:
        year = (
            voucher.purchase_date.year
            if voucher.purchase_date
            else timezone.now().year
        )

        counters[("PCV", year)] += 1
        counters[("PR", year)] += 1
        counters[("IAR", year)] += 1

        voucher.report_pcv_no = f"PCV-{year}-{counters[('PCV', year)]:04d}"
        voucher.report_pr_no = f"PR-{year}-{counters[('PR', year)]:04d}"
        voucher.report_iar_no = f"IAR-{year}-{counters[('IAR', year)]:04d}"

    return vouchers


def _get_previous_replenishment(fund, replenishment_obj=None):
    """
    Get the most recent released replenishment before the current one.
    If preview mode, get the latest released replenishment for the fund.
    """
    qs = Replenishment.objects.filter(
        fund=fund,
        status=ReplenishmentStatus.RELEASED
    )

    if replenishment_obj:
        qs = qs.filter(created_at__lt=replenishment_obj.created_at)

    return qs.order_by("-created_at").first()


def _get_previous_cash_on_hand(previous_replenishment):
    """
    Safely resolve previous cash on hand.
    Priority:
    1. stored cash_on_hand field if available
    2. opening_balance - total_expenses
    """
    stored_cash_on_hand = getattr(previous_replenishment, "cash_on_hand", None)
    if stored_cash_on_hand is not None:
        return stored_cash_on_hand

    opening_balance = previous_replenishment.opening_balance or Decimal("0.00")
    total_expenses = previous_replenishment.total_expenses or Decimal("0.00")

    computed_cash_on_hand = opening_balance - total_expenses
    return computed_cash_on_hand if computed_cash_on_hand >= Decimal("0.00") else Decimal("0.00")


def _get_voucher_amount(voucher):
    """
    Safe amount resolver for replenishment reporting.
    """
    actual_amount = getattr(voucher, "actual_amount", None)
    if actual_amount is not None:
        return actual_amount

    if voucher.amount_liquidated:
        return voucher.amount_liquidated

    return voucher.amount_requested or Decimal("0.00")


def build_replenishment_context(request):
    fund = PettyCashFund.objects.filter(
        custodian=request.user,
        is_active=True
    ).first()

    if not fund:
        return None

    replenishment_id = request.POST.get("replenishment_id")
    replenishment_obj = None

    # =========================================================
    # EXISTING REPLENISHMENT
    # =========================================================
    if replenishment_id:
        replenishment_obj = Replenishment.objects.filter(
            pk=replenishment_id,
            fund=fund
        ).first()

        if not replenishment_obj:
            return None

        vouchers_qs = replenishment_obj.vouchers.select_related(
            "expense_category",
            "requester"
        ).order_by("purchase_date", "created_at", "id")

        vouchers = _attach_report_display_numbers(list(vouchers_qs))

        derived_start = vouchers[0].purchase_date if vouchers else None
        derived_end = vouchers[-1].purchase_date if vouchers else None

        date_from = replenishment_obj.period_start or derived_start
        date_to = replenishment_obj.period_end or derived_end

        report_number = replenishment_obj.report_number
        sheet_number = replenishment_obj.sheet_number or 1
        replenishment_amount = replenishment_obj.total_expenses or Decimal("0.00")

    # =========================================================
    # LIVE PREVIEW MODE
    # =========================================================
    else:
        raw_date_from = request.POST.get("date_from", "").strip()
        raw_date_to = request.POST.get("date_to", "").strip()
        selected_ids = request.POST.getlist("selected_vouchers")

        date_from = parse_date(raw_date_from) if raw_date_from else None
        date_to = parse_date(raw_date_to) if raw_date_to else None

        vouchers_qs = PettyCashVoucher.objects.filter(
            fund=fund,
            is_posted_to_ledger=True,
            is_replenished=False
        )

        if date_from:
            vouchers_qs = vouchers_qs.filter(purchase_date__gte=date_from)

        if date_to:
            vouchers_qs = vouchers_qs.filter(purchase_date__lte=date_to)

        if selected_ids:
            vouchers_qs = vouchers_qs.filter(id__in=selected_ids)

        vouchers_qs = vouchers_qs.select_related(
            "expense_category",
            "requester"
        ).order_by("purchase_date", "created_at", "id")

        vouchers = _attach_report_display_numbers(list(vouchers_qs))

        if not vouchers:
            return None

        if not date_from:
            date_from = vouchers[0].purchase_date
        if not date_to:
            date_to = vouchers[-1].purchase_date

        replenishment_amount = Decimal("0.00")
        for voucher in vouchers:
            replenishment_amount += _get_voucher_amount(voucher)

        report_number = None
        sheet_number = 1

    # =========================================================
    # APPENDIX 50 – OPENING / PRIOR POSITION
    # =========================================================
    records = []
    previous_replenishment = _get_previous_replenishment(fund, replenishment_obj)

    if previous_replenishment:
        prev_cash_on_hand = _get_previous_cash_on_hand(previous_replenishment)
        prev_replenishment_amount = (
            previous_replenishment.check_amount
            or previous_replenishment.total_expenses
            or Decimal("0.00")
        )
        opening_balance = prev_cash_on_hand + prev_replenishment_amount

        # Row 1: A/O Cash-OnHand
        records.append({
            "date": previous_replenishment.period_end,
            "reference": "Cash-OnHand",
            "payee": "",
            "particulars": "",
            "received": None,
            "disbursement": None,
            "balance": prev_cash_on_hand,
        })

        # Row 2: Previous Replenishment
        records.append({
            "date": previous_replenishment.check_date or previous_replenishment.period_end,
            "reference": "Replenishment",
            "payee": "",
            "particulars": "",
            "received": prev_replenishment_amount,
            "disbursement": None,
            "balance": None,
        })

        # Row 3: Total
        records.append({
            "date": None,
            "reference": "Total",
            "payee": "",
            "particulars": "",
            "received": None,
            "disbursement": None,
            "balance": opening_balance,
        })

    else:
        # FIRST REPLENISHMENT
        first_date = date_from or (vouchers[0].purchase_date if vouchers else timezone.now().date())
        ao_date = first_date - timedelta(days=1) if first_date else None
        opening_balance = fund.fund_amount or Decimal("0.00")

        # Row 1: A/O Cash-OnHand = 0.00
        records.append({
            "date": ao_date,
            "reference": "Cash-OnHand",
            "payee": "",
            "particulars": "",
            "received": None,
            "disbursement": None,
            "balance": Decimal("0.00"),
        })

        # Row 2: Initial Fund
        records.append({
            "date": getattr(fund, "created_at", None).date() if getattr(fund, "created_at", None) else first_date,
            "reference": "Initial Fund",
            "payee": "",
            "particulars": "",
            "received": opening_balance,
            "disbursement": None,
            "balance": None,
        })

        # Row 3: Total
        records.append({
            "date": None,
            "reference": "Total",
            "payee": "",
            "particulars": "",
            "received": None,
            "disbursement": None,
            "balance": opening_balance,
        })

    # =========================================================
    # CURRENT EXPENSES
    # =========================================================
    running_balance = opening_balance

    for voucher in vouchers:
        amount = _get_voucher_amount(voucher)
        running_balance -= amount

        records.append({
            "date": voucher.purchase_date,
            "reference": getattr(voucher, "report_pcv_no", voucher.pcv_no),
            "payee": voucher.requester.get_full_name(),
            "particulars": voucher.expense_category.name if voucher.expense_category else "",
            "received": None,
            "disbursement": amount,
            "balance": running_balance,
        })

    # =========================================================
    # RECONCILIATION
    # =========================================================
    cash_on_hand = running_balance
    allocated_fund = fund.fund_amount or Decimal("0.00")
    reconciled_total = cash_on_hand + replenishment_amount

    # =========================================================
    # APPENDIX 51 REGISTER
    # =========================================================
    expense_category_ids = [
        voucher.expense_category_id
        for voucher in vouchers
        if voucher.expense_category_id
    ]

    expense_categories = ExpenseCategory.objects.filter(
        id__in=expense_category_ids
    ).order_by("code")

    category_totals = defaultdict(lambda: Decimal("0.00"))
    register_rows = []

    register_running_balance = opening_balance

    for voucher in vouchers:
        amount = _get_voucher_amount(voucher)
        register_running_balance -= amount

        breakdown = defaultdict(lambda: None)

        if voucher.expense_category_id:
            breakdown[voucher.expense_category.id] = amount
            category_totals[voucher.expense_category.id] += amount

        register_rows.append({
            "date": voucher.purchase_date,
            "reference": getattr(voucher, "report_pcv_no", voucher.pcv_no),
            "particulars": voucher.expense_category.name if voucher.expense_category else "",
            "receipt": None,
            "payment": amount,
            "balance": register_running_balance,
            "breakdown": breakdown,
        })

    return {
        "fund": fund,
        "vouchers": vouchers,
        "records": records,
        "register_rows": register_rows,
        "expense_categories": expense_categories,
        "category_totals": category_totals,

        "report_number": report_number,
        "sheet_number": sheet_number,

        "opening_balance": opening_balance,
        "previous_balance": opening_balance,
        "cash_on_hand": cash_on_hand,
        "replenishment_amount": replenishment_amount,
        "reconciled_total": reconciled_total,
        "allocated_fund": allocated_fund,

        "total": replenishment_amount,
        "generated_date": timezone.now(),

        "date_from": date_from,
        "date_to": date_to,
        "period_start": date_from,
        "period_end": date_to,

        "selected_count": len(vouchers),
    }