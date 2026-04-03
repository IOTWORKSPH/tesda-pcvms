# pettycash/management/commands/full_reset_dev.py

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

from pettycash.models import (
    PettyCashVoucher,
    PCVItem,
    ReceiptAttachment,
    Replenishment,
    LiquidationReview,
    Notification,
)

from finance.models import LedgerEntry, PettyCashFund
from audit.models import AuditLog


class Command(BaseCommand):
    help = "⚠ DEV ONLY: FULL database reset except master data"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):

        if not settings.DEBUG:
            self.stdout.write(
                self.style.ERROR("❌ Allowed only in DEBUG mode.")
            )
            return

        if not options["force"]:
            confirm = input(
                "⚠ This will DELETE ALL TRANSACTIONS. Continue? (yes/no): "
            )
            if confirm.lower() != "yes":
                self.stdout.write(self.style.WARNING("Cancelled."))
                return

        self.stdout.write(self.style.WARNING("Starting FULL DEV RESET..."))

        # ===============================
        # DELETE TRANSACTIONAL DATA
        # ===============================

        LiquidationReview.objects.all().delete()
        Notification.objects.all().delete()
        AuditLog.objects.all().delete()

        ReceiptAttachment.objects.all().delete()
        PCVItem.objects.all().delete()
        PettyCashVoucher.objects.all().delete()
        Replenishment.objects.all().delete()
        LedgerEntry.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS("✔ Transactional records deleted.")
        )

        # ===============================
        # RESET FUND BALANCES
        # ===============================

        for fund in PettyCashFund.objects.all():
            fund.current_balance = fund.fund_amount
            fund.save(update_fields=["current_balance"])

        self.stdout.write(
            self.style.SUCCESS("✔ Fund balances restored.")
        )

        # ===============================
        # RESET AUTO_INCREMENT (MySQL)
        # ===============================

        with connection.cursor() as cursor:

            tables = [
                "pettycash_pettycashvoucher",
                "pettycash_pcvitem",
                "pettycash_receiptattachment",
                "pettycash_replenishment",
                "pettycash_liquidationreview",
                "finance_ledgerentry",
                "audit_auditlog",
                "pettycash_notification",
            ]

            for table in tables:
                cursor.execute(
                    f"ALTER TABLE {table} AUTO_INCREMENT = 1;"
                )

        self.stdout.write(
            self.style.SUCCESS("✔ AUTO_INCREMENT reset.")
        )

        self.stdout.write(
            self.style.SUCCESS("🎉 FULL DEV RESET COMPLETED.")
        )