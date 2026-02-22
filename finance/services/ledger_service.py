
#Finance/Services/ledger_service.py codes
from django.db import transaction
from decimal import Decimal

from finance.models import LedgerEntry, ReferenceType, PettyCashFund
from pettycash.models import TransactionType, VoucherStatus
from audit.services.audit_service import AuditService
from audit.models import AuditAction


class LedgerService:
    """
    Government-Grade Financial Posting Engine
    ------------------------------------------
    • Atomic
    • Concurrency-safe
    • Audit compliant
    • Prevents double posting
    • Protects fund balance integrity
    """

    # ======================================================
    # INTERNAL: LOCK FUND ROW (Prevents concurrent posting)
    # ======================================================

    @staticmethod
    def _lock_fund(fund_id):
        return PettyCashFund.objects.select_for_update().get(pk=fund_id)

    # ======================================================
    # POST REIMBURSEMENT
    # ======================================================

    @staticmethod
    @transaction.atomic
    def post_reimbursement(voucher, user):

        if voucher.is_posted_to_ledger:
            raise ValueError("Voucher already posted.")

        if voucher.status != VoucherStatus.APPROVED:
            raise ValueError("Voucher must be approved before posting.")

        if voucher.transaction_type != TransactionType.REIMBURSEMENT:
            raise ValueError("Invalid transaction type for reimbursement.")

        # Lock fund row
        fund = LedgerService._lock_fund(voucher.fund.id)

        amount = voucher.amount_requested

        if fund.current_balance < amount:
            raise ValueError("Insufficient fund balance.")

        previous_status = voucher.status

        new_balance = fund.current_balance - amount

        LedgerEntry.objects.create(
            fund=fund,
            transaction_date=voucher.purchase_date,
            debit=Decimal("0.00"),
            credit=amount,
            running_balance=new_balance,
            reference_type=ReferenceType.PCV,
            reference_no=voucher.pcv_no,
            description=f"Reimbursement - {voucher.purpose}",
            created_by=user,
        )

        fund.current_balance = new_balance
        fund.save(update_fields=["current_balance"])

        voucher.is_posted_to_ledger = True
        voucher.status = VoucherStatus.POSTED
        voucher.save(update_fields=["is_posted_to_ledger", "status"])

        # Audit log
        AuditService.log(
            entity=voucher.entity,
            user=user,
            action=AuditAction.POSTING,
            model_name="PettyCashVoucher",
            object_id=voucher.pcv_no,
            description="Reimbursement posted to ledger",
            previous_status=previous_status,
            new_status=voucher.status
        )

        return True

    # ======================================================
    # POST CASH ADVANCE RELEASE
    # ======================================================

    @staticmethod
    @transaction.atomic
    def post_cash_advance_release(voucher, user):

        if voucher.is_posted_to_ledger:
            raise ValueError("Voucher already posted.")

        if voucher.status != VoucherStatus.APPROVED:
            raise ValueError("Voucher must be approved before release.")

        if voucher.transaction_type != TransactionType.CASH_ADVANCE:
            raise ValueError("Invalid transaction type for cash advance.")

        fund = LedgerService._lock_fund(voucher.fund.id)

        amount = voucher.amount_requested

        if fund.current_balance < amount:
            raise ValueError("Insufficient fund balance.")

        previous_status = voucher.status

        new_balance = fund.current_balance - amount

        LedgerEntry.objects.create(
            fund=fund,
            transaction_date=voucher.created_at.date(),
            debit=Decimal("0.00"),
            credit=amount,
            running_balance=new_balance,
            reference_type=ReferenceType.PCV,
            reference_no=voucher.pcv_no,
            description="Cash Advance Release",
            created_by=user,
        )

        fund.current_balance = new_balance
        fund.save(update_fields=["current_balance"])

        voucher.status = VoucherStatus.RELEASED
        voucher.is_release_posted = True
        voucher.save(update_fields=["status", "is_posted_to_ledger"])

        # Audit log
        AuditService.log(
            entity=voucher.entity,
            user=user,
            action=AuditAction.RELEASE,
            model_name="PettyCashVoucher",
            object_id=voucher.pcv_no,
            description="Cash advance released and posted to ledger",
            previous_status=previous_status,
            new_status=voucher.status
        )

        return True

    # ======================================================
    # HANDLE LIQUIDATION ADJUSTMENT
    # ======================================================

    @staticmethod
    @transaction.atomic
    def post_liquidation_adjustment(voucher, user):

        if voucher.status != VoucherStatus.LIQUIDATED:
            raise ValueError("Voucher must be liquidated first.")

        fund = LedgerService._lock_fund(voucher.fund.id)

        requested = voucher.amount_requested
        actual = voucher.amount_liquidated

        difference = requested - actual
        previous_status = voucher.status

        # No adjustment needed
        if difference == 0:

            voucher.status = VoucherStatus.POSTED
            voucher.is_posted_to_ledger = True
            voucher.is_liquidation_posted = True

            voucher.save(update_fields=[
                "status",
                "is_posted_to_ledger",
                "is_liquidation_posted"
            ])

            AuditService.log(
                entity=voucher.entity,
                user=user,
                action=AuditAction.POSTING,
                model_name="PettyCashVoucher",
                object_id=voucher.pcv_no,
                description="Liquidation finalized (no adjustment needed)",
                previous_status=previous_status,
                new_status=voucher.status
            )

            return True

        # ============================================
        # EXCESS CASH RETURNED (Debit Fund)
        # ============================================
        if difference > 0:

            new_balance = fund.current_balance + difference

            LedgerEntry.objects.create(
                fund=fund,
                transaction_date=voucher.created_at.date(),
                debit=difference,
                credit=Decimal("0.00"),
                running_balance=new_balance,
                reference_type=ReferenceType.ADJUSTMENT,
                reference_no=f"{voucher.pcv_no}-EXCESS",
                description="Excess cash returned",
                created_by=user,
            )

            fund.current_balance = new_balance
            fund.save(update_fields=["current_balance"])

        # ============================================
        # SHORTAGE (Credit Fund)
        # ============================================
        elif difference < 0:

            shortage = abs(difference)

            if fund.current_balance < shortage:
                raise ValueError("Insufficient fund balance for shortage adjustment.")

            new_balance = fund.current_balance - shortage

            LedgerEntry.objects.create(
                fund=fund,
                transaction_date=voucher.created_at.date(),
                debit=Decimal("0.00"),
                credit=shortage,
                running_balance=new_balance,
                reference_type=ReferenceType.ADJUSTMENT,
                reference_no=f"{voucher.pcv_no}-SHORTAGE",
                description="Shortage reimbursement",
                created_by=user,
            )

            fund.current_balance = new_balance
            fund.save(update_fields=["current_balance"])

        voucher.status = VoucherStatus.POSTED
        voucher.is_posted_to_ledger = True
        voucher.save(update_fields=["status", "is_posted_to_ledger"])

        # Audit log
        AuditService.log(
            entity=voucher.entity,
            user=user,
            action=AuditAction.ADJUSTMENT,
            model_name="PettyCashVoucher",
            object_id=voucher.pcv_no,
            description="Liquidation adjustment posted",
            previous_status=previous_status,
            new_status=voucher.status
        )

        return True