# pettycash/services/dashboard_service.py

from decimal import Decimal
from datetime import date

from django.db.models import Sum, Q
from django.utils import timezone

from pettycash.models import (
    PettyCashVoucher,
    VoucherStatus,
    TransactionType,
)

from finance.models import LedgerEntry

class CustodianDashboardService:

    @staticmethod
    def get_dashboard_data(fund):

        today = timezone.now().date()

        total_fund = fund.fund_amount
        current_balance = fund.current_balance

        # =========================================
        # FUND UTILIZATION
        # =========================================

        utilized_amount = total_fund - current_balance

        if total_fund > 0:
            utilization_percent = (utilized_amount / total_fund) * 100
        else:
            utilization_percent = 0

        # =========================================
        # APPROVED – FOR RELEASE
        # =========================================

        for_release = PettyCashVoucher.objects.filter(
            fund=fund,
            status=VoucherStatus.APPROVED,
            transaction_type=TransactionType.CASH_ADVANCE
        ).select_related("requester")

        # =========================================
        # APPROVED – FOR REIMBURSEMENT
        # =========================================

        for_reimbursement = PettyCashVoucher.objects.filter(
            fund=fund,
            status=VoucherStatus.APPROVED,
            transaction_type=TransactionType.REIMBURSEMENT
        ).select_related("requester")

        # =========================================
        # RELEASED – FOR LIQUIDATION FINALIZATION
        # =========================================

        for_liquidation = PettyCashVoucher.objects.filter(
            fund=fund,
            status=VoucherStatus.LIQUIDATED,
            transaction_type=TransactionType.CASH_ADVANCE
        ).select_related("requester")

        # =========================================
        # UNLIQUIDATED (AGING)
        # =========================================

        unliquidated = PettyCashVoucher.objects.filter(
            fund=fund,
            status=VoucherStatus.RELEASED,
            transaction_type=TransactionType.CASH_ADVANCE
        )

        aging_data = []
        for voucher in unliquidated:
            if voucher.release_date:
                days = (today - voucher.release_date.date()).days
            else:
                days = 0

            if days > 30:
                risk = "danger"
            elif days > 15:
                risk = "warning"
            else:
                risk = "normal"

            aging_data.append({
                "voucher": voucher,
                "days": days,
                "risk": risk
            })

        # =========================================
        # LEDGER SNAPSHOT
        # =========================================

        ledger_snapshot = LedgerEntry.objects.filter(
            fund=fund
        ).order_by("-transaction_date", "-id")[:5]

        # =========================================
        # REPLENISHMENT ALERT
        # =========================================

        replenish_threshold = total_fund * Decimal("0.30")
        is_ready_for_replenishment = current_balance <= replenish_threshold

        return {
            "total_fund": total_fund,
            "current_balance": current_balance,
            "utilized_amount": utilized_amount,
            "utilization_percent": round(utilization_percent, 2),
            "for_release": for_release,
            "for_reimbursement": for_reimbursement,
            "for_liquidation": for_liquidation,
            "aging_data": aging_data,
            "ledger_snapshot": ledger_snapshot,
            "is_ready_for_replenishment": is_ready_for_replenishment,
        }
