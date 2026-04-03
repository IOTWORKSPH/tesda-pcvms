from django.utils.dateparse import parse_date
from django.utils import timezone
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
    counters = defaultdict(int)

    for voucher in vouchers:
        year = voucher.purchase_date.year if voucher.purchase_date else timezone.now().year

        counters[("PCV", year)] += 1
        counters[("PR", year)] += 1
        counters[("IAR", year)] += 1

        voucher.report_pcv_no = f"PCV-{year}-{counters[('PCV', year)]:04d}"
        voucher.report_pr_no = f"PR-{year}-{counters[('PR', year)]:04d}"
        voucher.report_iar_no = f"IAR-{year}-{counters[('IAR', year)]:04d}"

    return vouchers


def build_replenishment_context(request):

    fund = PettyCashFund.objects.filter(
        custodian=request.user,
        is_active=True
    ).first()

    if not fund:
        return None

    replenishment_id = request.POST.get("replenishment_id")
    replenishment_obj = None

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

        if vouchers:
            derived_start = vouchers[0].purchase_date
            derived_end = vouchers[-1].purchase_date
        else:
            derived_start = None
            derived_end = None

        date_from = replenishment_obj.period_start or derived_start
        date_to = replenishment_obj.period_end or derived_end

        report_number = replenishment_obj.report_number
        sheet_number = replenishment_obj.sheet_number
        opening_balance = replenishment_obj.opening_balance
        replenishment_amount = replenishment_obj.total_expenses

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
        for v in vouchers:
            replenishment_amount += v.actual_amount

        opening_balance = fund.current_balance
        report_number = None
        sheet_number = 1

    records = []
    previous_replenishment = None

    if replenishment_obj:
        previous_replenishment = (
            Replenishment.objects
            .filter(
                fund=fund,
                status=ReplenishmentStatus.RELEASED,
                created_at__lt=replenishment_obj.created_at
            )
            .order_by("-created_at")
            .first()
        )

    if previous_replenishment:
        prev_cash_on_hand = previous_replenishment.cash_on_hand
        prev_check_amount = previous_replenishment.check_amount

        records.append({
            "date": previous_replenishment.period_end,
            "reference": "A/O",
            "payee": "",
            "particulars": "Cash on Hand",
            "received": None,
            "disbursement": None,
            "balance": prev_cash_on_hand,
        })

        new_balance = prev_cash_on_hand + prev_check_amount

        records.append({
            "date": previous_replenishment.check_date,
            "reference": previous_replenishment.check_number,
            "payee": "",
            "particulars": f"Replenishment {previous_replenishment.report_number}",
            "received": prev_check_amount,
            "disbursement": None,
            "balance": new_balance,
        })

        running_balance = new_balance

    else:
        running_balance = fund.fund_amount

        records.append({
            "date": None,
            "reference": "INITIAL FUND",
            "payee": "",
            "particulars": "Initial Fund Allocation",
            "received": fund.fund_amount,
            "disbursement": None,
            "balance": fund.fund_amount,
        })

    for voucher in vouchers:
        amount = voucher.actual_amount
        running_balance -= amount

        records.append({
            "date": voucher.purchase_date,
            "reference": getattr(voucher, "report_pcv_no", voucher.pcv_no),
            "payee": voucher.requester.get_full_name(),
            "particulars": voucher.expense_category.name,
            "received": None,
            "disbursement": amount,
            "balance": running_balance,
        })

    cash_on_hand = running_balance
    allocated_fund = fund.fund_amount
    reconciled_total = cash_on_hand + replenishment_amount

    expense_category_ids = [
        v.expense_category_id
        for v in vouchers
        if v.expense_category_id
    ]

    expense_categories = ExpenseCategory.objects.filter(
        id__in=expense_category_ids
    ).order_by("code")

    category_totals = defaultdict(lambda: Decimal("0.00"))
    register_rows = []

    register_running_balance = opening_balance

    for voucher in vouchers:
        amount = voucher.actual_amount
        register_running_balance -= amount

        breakdown = defaultdict(lambda: None)
        breakdown[voucher.expense_category.id] = amount
        category_totals[voucher.expense_category.id] += amount

        register_rows.append({
            "date": voucher.purchase_date,
            "reference": getattr(voucher, "report_pcv_no", voucher.pcv_no),
            "particulars": voucher.expense_category.name,
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
        "previous_balance": opening_balance,
        "cash_on_hand": cash_on_hand,
        "replenishment_amount": replenishment_amount,
        "reconciled_total": reconciled_total,
        "allocated_fund": allocated_fund,
        "total": replenishment_amount,
        "generated_date": timezone.now(),
        "date_from": date_from,
        "date_to": date_to,
        "selected_count": len(vouchers),
    }