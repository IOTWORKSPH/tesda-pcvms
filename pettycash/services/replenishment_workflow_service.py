# pettycash/services/replenishment_workflow_service.py

from django.db import transaction
from django.db.models import Sum, Max
from django.utils import timezone
from decimal import Decimal

from pettycash.models import (
    PettyCashVoucher,
    Replenishment,
    ReplenishmentStatus,
    VoucherStatus,
)
from finance.models import LedgerEntry, ReferenceType, PettyCashFund


class ReplenishmentWorkflowService:
    """
    Full Government Replenishment Lifecycle Service
    ------------------------------------------------
    • Safe
    • Concurrency-protected
    • Audit-ready
    • Status-driven
    """

    # =====================================================
    # ELIGIBLE VOUCHERS
    # =====================================================

    @staticmethod
    def get_eligible_vouchers(fund, date_from=None, date_to=None):

        qs = PettyCashVoucher.objects.filter(
            fund=fund,
            status=VoucherStatus.POSTED,
            is_replenished=False
        )

        if date_from:
            qs = qs.filter(purchase_date__gte=date_from)

        if date_to:
            qs = qs.filter(purchase_date__lte=date_to)

        return qs.select_related("expense_category", "requester")

    # =====================================================
    # GENERATE REPLENISHMENT (DRAFT)
    # =====================================================

    @staticmethod
    @transaction.atomic
    def generate_replenishment(fund, vouchers, date_from, date_to, user):

        if not vouchers.exists():
            raise ValueError("No eligible vouchers found.")

        # Lock fund row
        fund = PettyCashFund.objects.select_for_update().get(pk=fund.pk)

        total_expenses = vouchers.aggregate(
            total=Sum("amount_requested")
        )["total"] or Decimal("0.00")

        # Opening balance snapshot
        latest_entry = fund.ledger_entries.order_by(
            "-transaction_date", "-id"
        ).first()

        opening_balance = (
            latest_entry.running_balance
            if latest_entry
            else fund.current_balance
        )

        current_year = timezone.now().year

        last_series = (
            Replenishment.objects
            .select_for_update()
            .filter(year=current_year, fund=fund)
            .aggregate(Max("series_number"))
        )["series_number__max"] or 0

        next_series = last_series + 1
        report_number = f"{current_year}-{next_series:04d}"

        replenishment = Replenishment.objects.create(
            fund=fund,
            year=current_year,
            series_number=next_series,
            report_number=report_number,
            opening_balance=opening_balance,
            total_expenses=total_expenses,
            period_start=date_from,
            period_end=date_to,
            status=ReplenishmentStatus.DRAFT,
            created_by=user,
        )

        vouchers.update(replenishment=replenishment)

        return replenishment

    # =====================================================
    # SUBMIT
    # =====================================================

    @staticmethod
    @transaction.atomic
    def submit(replenishment):

        if replenishment.status != ReplenishmentStatus.DRAFT:
            raise ValueError("Only draft replenishments can be submitted.")

        replenishment.status = ReplenishmentStatus.SUBMITTED_TO_ACCOUNTING
        replenishment.save(update_fields=["status"])

    # =====================================================
    # APPROVE
    # =====================================================

    @staticmethod
    @transaction.atomic
    def approve(replenishment):

        if replenishment.status != ReplenishmentStatus.SUBMITTED:
            raise ValueError("Replenishment must be submitted first.")

        replenishment.status = ReplenishmentStatus.APPROVED
        replenishment.save(update_fields=["status"])

    # =====================================================
    # RELEASE (FINANCIAL POSTING)
    # =====================================================

    @staticmethod
    @transaction.atomic
    def release(replenishment, check_number, check_date, user):

        if replenishment.status != ReplenishmentStatus.SUBMITTED_TO_ACCOUNTING:
            raise ValueError("Replenishment must be submitted first.")

        fund = PettyCashFund.objects.select_for_update().get(
            pk=replenishment.fund.pk
        )

        amount = replenishment.total_expenses

        # Update fund balance
        last_entry = (
            LedgerEntry.objects
            .filter(fund=fund)
            .order_by("-transaction_date", "-id")
            .first()
        )

        previous_balance = (
            last_entry.running_balance
            if last_entry
            else fund.fund_amount
        )

        new_balance = previous_balance + amount
        fund.current_balance = new_balance
        fund.save(update_fields=["current_balance"])

        # Create ledger entry
        LedgerEntry.objects.create(
            fund=fund,
            transaction_date=check_date,
            debit=amount,
            credit=Decimal("0.00"),
            running_balance=new_balance,
            reference_type=ReferenceType.REPLENISHMENT,
            reference_no=replenishment.report_number,
            description=f"Replenishment - Check #{check_number}",
            created_by=user,
        )

        # Update vouchers
        replenishment.vouchers.update(is_replenished=True)

        # Update replenishment
        replenishment.check_number = check_number
        replenishment.check_date = check_date
        replenishment.check_amount = amount
        replenishment.status = ReplenishmentStatus.RELEASED
        replenishment.save(
            update_fields=[
                "check_number",
                "check_date",
                "check_amount",
                "status",
            ]
        )