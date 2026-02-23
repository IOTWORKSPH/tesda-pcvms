# pettycash/services/replenishment_builder.py

from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from collections import defaultdict

from finance.models import PettyCashFund, LedgerEntry, ReferenceType
from pettycash.models import PettyCashVoucher, ExpenseCategory


def build_replenishment_context(request):

    fund = PettyCashFund.objects.filter(
        custodian=request.user,
        is_active=True
    ).first()

    if not fund:
        return None

    raw_date_from = request.GET.get("date_from", "").strip()
    raw_date_to = request.GET.get("date_to", "").strip()

    date_from = parse_date(raw_date_from) if raw_date_from else None
    date_to = parse_date(raw_date_to) if raw_date_to else None

    vouchers = PettyCashVoucher.objects.filter(
        fund=fund,
        is_posted_to_ledger=True
    )

    if date_from:
        vouchers = vouchers.filter(purchase_date__gte=date_from)

    if date_to:
        vouchers = vouchers.filter(purchase_date__lte=date_to)

    vouchers = vouchers.select_related(
        "expense_category",
        "requester"
    ).order_by("purchase_date")

    total = vouchers.aggregate(
        total=Sum("amount_requested")
    )["total"] or Decimal("0.00")

    # ===========================
    # Ledger Records (Appendix 50)
    # ===========================
    entries = LedgerEntry.objects.filter(
        fund=fund
    ).order_by("transaction_date", "id")

    records = []

    for entry in entries:

        payee = ""
        particulars = ""

        if entry.reference_type == ReferenceType.PCV:
            voucher = vouchers.filter(
                pcv_no=entry.reference_no
            ).first()

            if voucher:
                payee = voucher.requester.get_full_name()
                particulars = voucher.expense_category.name

        elif entry.reference_type == ReferenceType.REPLENISHMENT:
            particulars = "Replenishment"

        else:
            particulars = entry.description or ""

        records.append({
            "date": entry.transaction_date,
            "reference": entry.reference_no,
            "payee": payee,
            "particulars": particulars,
            "received": entry.debit if entry.debit > 0 else None,
            "disbursement": entry.credit if entry.credit > 0 else None,
            "balance": entry.running_balance,
        })

    # ===========================
    # Appendix 51 Register
    # ===========================
    expense_categories = ExpenseCategory.objects.filter(
        id__in=vouchers.values_list("expense_category_id", flat=True)
    ).order_by("code")

    category_totals = defaultdict(lambda: Decimal("0.00"))
    register_rows = []

    for entry in entries.filter(reference_type=ReferenceType.PCV):

        voucher = vouchers.filter(
            pcv_no=entry.reference_no
        ).first()

        if not voucher:
            continue

        breakdown = defaultdict(lambda: None)
        amount = entry.credit

        breakdown[voucher.expense_category.id] = amount
        category_totals[voucher.expense_category.id] += amount

        register_rows.append({
            "date": entry.transaction_date,
            "reference": entry.reference_no,
            "particulars": voucher.expense_category.name,
            "receipt": entry.debit if entry.debit > 0 else None,
            "payment": entry.credit if entry.credit > 0 else None,
            "balance": entry.running_balance,
            "breakdown": breakdown,
        })

    return {
        "fund": fund,
        "vouchers": vouchers,
        "total": total,
        "records": records,
        "register_rows": register_rows,
        "expense_categories": expense_categories,
        "category_totals": category_totals,
        "generated_date": timezone.now(),
        "date_from": date_from,
        "date_to": date_to,
    }