
#PettyCash/Services/workflow_service.py codes
from django.db import transaction
from pettycash.models import VoucherStatus, TransactionType
from finance.services.ledger_service import LedgerService

from audit.services.audit_service import AuditService
from audit.models import AuditAction
from pettycash.services.numbering_service import DocumentNumberService

class WorkflowService:
    """
    Controls all state transitions for Petty Cash Voucher.
    Enforces role checks and triggers financial postings.
    """

    # =====================================================
    # SUBMIT FOR APPROVAL
    # =====================================================

    @staticmethod
    def submit_for_approval(voucher, user):

        if voucher.status != VoucherStatus.DRAFT:
            raise ValueError("Only draft vouchers can be submitted.")

        voucher.status = VoucherStatus.FOR_APPROVAL
        voucher.save()

        return True

    # =====================================================
    # APPROVE VOUCHER
    # =====================================================

    @staticmethod
    @transaction.atomic
    def approve(voucher, user):

        if voucher.status != VoucherStatus.FOR_APPROVAL:
            raise ValueError("Voucher not ready for approval.")

        if not user.has_role("Administrator") and not user.is_system_admin:
            raise PermissionError("Not authorized.")

        previous_status = voucher.status

        # ===============================
        # GENERATE PCV NUMBER
        # ===============================
        if not voucher.pcv_no:
            voucher.pcv_no = DocumentNumberService.generate(
                voucher.entity,
                "PCV"
            )

        # ==========================================
        # NEW: GENERATE PR & IAR FOR REIMBURSEMENT
        # ==========================================
        if voucher.transaction_type == TransactionType.REIMBURSEMENT:

            if not voucher.pr_no:
                voucher.pr_no = DocumentNumberService.generate(
                    voucher.entity,
                    "PR"
                )

            if not voucher.iar_no:
                voucher.iar_no = DocumentNumberService.generate(
                    voucher.entity,
                    "IAR"
                )

        voucher.status = VoucherStatus.APPROVED
        voucher.save()

        # ===============================
        # AUDIT LOG
        # ===============================
        AuditService.log(
            entity=voucher.entity,
            user=user,
            action=AuditAction.APPROVAL,
            model_name="PettyCashVoucher",
            object_id=voucher.pcv_no,
            description="Voucher approved",
            previous_status=previous_status,
            new_status=voucher.status
        )

        return True

    # =====================================================
    # RELEASE CASH (FOR CASH ADVANCE ONLY)
    # =====================================================

    @staticmethod
    @transaction.atomic
    def release_cash(voucher, user):

        if voucher.transaction_type != TransactionType.CASH_ADVANCE:
            raise ValueError("Release only allowed for cash advance.")

        if voucher.status != VoucherStatus.APPROVED:
            raise ValueError("Voucher must be approved first.")

        if not user.has_role("Custodian") and not user.is_system_admin:
            raise PermissionError("Only custodian can release cash.")

        # Post to ledger
        LedgerService.post_cash_advance_release(voucher, user)

        return True

    # =====================================================
    # POST REIMBURSEMENT
    # =====================================================

    @staticmethod
    @transaction.atomic
    def post_reimbursement(voucher, user):

        if voucher.transaction_type != TransactionType.REIMBURSEMENT:
            raise ValueError("Invalid transaction type.")

        if voucher.status != VoucherStatus.APPROVED:
            raise ValueError("Voucher must be approved first.")

        if not user.has_role("Custodian") and not user.is_system_admin:
            raise PermissionError("Only custodian can post reimbursement.")

        LedgerService.post_reimbursement(voucher, user)

        return True

    # =====================================================
    # LIQUIDATE CASH ADVANCE
    # =====================================================

    @staticmethod
    @transaction.atomic
    def liquidate(voucher, user):

        if voucher.transaction_type != TransactionType.CASH_ADVANCE:
            raise ValueError("Only cash advances can be liquidated.")

        if voucher.status != VoucherStatus.RELEASED:
            raise ValueError("Voucher must be released first.")

        # =========================================
        # 🔢 GENERATE PR & IAR ON LIQUIDATION
        # =========================================
        if not voucher.pr_no:
            voucher.pr_no = DocumentNumberService.generate(
                voucher.entity,
                "PR"
            )

        if not voucher.iar_no:
            voucher.iar_no = DocumentNumberService.generate(
                voucher.entity,
                "IAR"
            )

        voucher.status = VoucherStatus.LIQUIDATED
        voucher.save()

        return True

    # =====================================================
    # FINALIZE LIQUIDATION (POST ADJUSTMENT)
    # =====================================================

    @staticmethod
    @transaction.atomic
    def finalize_liquidation(voucher, user):

        if voucher.status != VoucherStatus.LIQUIDATED:
            raise ValueError("Voucher must be liquidated first.")

        if not user.has_role("Custodian") and not user.is_system_admin:
            raise PermissionError("Only custodian can finalize liquidation.")

        LedgerService.post_liquidation_adjustment(voucher, user)

        return True
