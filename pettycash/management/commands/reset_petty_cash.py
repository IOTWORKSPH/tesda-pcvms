from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from django.utils import timezone

from pettycash.models import (
    PettyCashVoucher,
    PCVItem,
    ReceiptAttachment,
    Replenishment,
)

from finance.models import (
    PettyCashFund,
    LedgerEntry,
    ReferenceType,
)

from users.models import Entity


class Command(BaseCommand):
    help = "Reset petty cash data for a specific entity"

    def add_arguments(self, parser):
        parser.add_argument(
            "--entity",
            type=str,
            required=True,
            help="Entity code (example: PTC-ZS)"
        )

    @transaction.atomic
    def handle(self, *args, **kwargs):

        entity_code = kwargs["entity"]

        try:
            entity = Entity.objects.get(code=entity_code)
        except Entity.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Entity '{entity_code}' not found.")
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"Resetting petty cash data for entity: {entity.code}"
            )
        )

        # -----------------------------------
        # Delete PCV Items
        # -----------------------------------
        items_deleted, _ = PCVItem.objects.filter(
            voucher__entity=entity
        ).delete()

        # -----------------------------------
        # Delete Receipts
        # -----------------------------------
        receipts_deleted, _ = ReceiptAttachment.objects.filter(
            voucher__entity=entity
        ).delete()

        # -----------------------------------
        # Delete Vouchers
        # -----------------------------------
        vouchers_deleted, _ = PettyCashVoucher.objects.filter(
            entity=entity
        ).delete()

        # -----------------------------------
        # Delete Replenishments
        # -----------------------------------
        repl_deleted, _ = Replenishment.objects.filter(
            fund__entity=entity
        ).delete()

        # -----------------------------------
        # Delete Ledger Entries
        # -----------------------------------
        ledger_deleted, _ = LedgerEntry.objects.filter(
            fund__entity=entity
        ).delete()

        # -----------------------------------
        # RESET FUNDS (DO NOT DELETE)
        # -----------------------------------
        funds = PettyCashFund.objects.filter(entity=entity)

        for fund in funds:
            fund.current_balance = fund.fund_amount
            fund.save(update_fields=["current_balance"])

            LedgerEntry.objects.create(
                fund=fund,
                transaction_date=timezone.now().date(),
                debit=fund.fund_amount,
                credit=Decimal("0.00"),
                running_balance=fund.fund_amount,
                reference_type=ReferenceType.ADJUSTMENT,
                reference_no="RESET-OPENING",
                description="Opening balance restored after petty cash reset",
                created_by=fund.custodian
            )

        # -----------------------------------
        # OUTPUT SUMMARY
        # -----------------------------------
        self.stdout.write(self.style.SUCCESS(f"✔ Deleted {items_deleted} items"))
        self.stdout.write(self.style.SUCCESS(f"✔ Deleted {receipts_deleted} receipts"))
        self.stdout.write(self.style.SUCCESS(f"✔ Deleted {vouchers_deleted} vouchers"))
        self.stdout.write(self.style.SUCCESS(f"✔ Deleted {repl_deleted} replenishments"))
        self.stdout.write(self.style.SUCCESS(f"✔ Deleted {ledger_deleted} ledger entries"))
        self.stdout.write(self.style.SUCCESS("✔ Fund balances reset"))

        self.stdout.write(
            self.style.SUCCESS(
                f"🎉 Petty cash reset completed for entity: {entity.code}"
            )
        )