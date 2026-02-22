from django.db.models import Sum
from pettycash.models import PettyCashVoucher, VoucherStatus, TransactionType
from datetime import datetime


class ReplenishmentService:

    @staticmethod
    def get_replenishment_data(fund, date_from=None, date_to=None):

        vouchers = PettyCashVoucher.objects.filter(
            fund=fund,
            status=VoucherStatus.LIQUIDATED
        )

        # ===============================
        # SAFE DATE FILTERING
        # ===============================

        if date_from:
            try:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                vouchers = vouchers.filter(
                    transaction_date__gte=date_from
                )
            except ValueError:
                pass

        if date_to:
            try:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
                vouchers = vouchers.filter(
                    transaction_date__lte=date_to
                )
            except ValueError:
                pass

        vouchers = vouchers.select_related(
            "requester",
            "expense_category"
        ).order_by("transaction_date")

        total_amount = vouchers.aggregate(
            total=Sum("total_items_amount")
        )["total"] or 0

        return {
            "vouchers": vouchers,
            "total_amount": total_amount,
        }
