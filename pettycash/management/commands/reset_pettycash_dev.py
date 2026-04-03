#pettycash/management/commands/reset_pettycash_dev.py

# ⚠ WARNING: DEVELOPMENT USE ONLY

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from django.conf import settings

from pettycash.models import (
    PettyCashVoucher,
    Replenishment,
    VoucherStatus,
    Notification,   # ← assuming notification model is here
)

from finance.models import LedgerEntry, PettyCashFund
from audit.models import AuditLog


class Command(BaseCommand):
    help = "⚠ DEV ONLY: Reset Petty Cash System (vouchers to draft, delete ledger, replenishment, audit logs, notifications)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force reset without confirmation",
        )

    @transaction.atomic
    def handle(self, *args, **options):

        if not settings.DEBUG:
            self.stdout.write(self.style.ERROR("❌ This command is allowed only in DEBUG mode."))
            return

        if not options["force"]:
            confirm = input("⚠ Are you sure you want to reset Petty Cash DEV data? (yes/no): ")
            if confirm.lower() != "yes":
                self.stdout.write(self.style.WARNING("Reset cancelled."))
                return

        self.stdout.write(self.style.WARNING("Starting Petty Cash DEV Reset..."))

        # ---------------------------------------------------
        # 1️⃣ Reset All Vouchers to Draft
        # ---------------------------------------------------
        vouchers_updated = PettyCashVoucher.objects.update(
            status=VoucherStatus.DRAFT,
            is_posted_to_ledger=False,
            is_release_posted=False,
            is_liquidation_posted=False,
            is_replenished=False,
            replenishment=None,
            release_date=None,
            released_by=None,
            amount_liquidated=Decimal("0.00"),
            pr_no=None,
            iar_no=None,
        )

        self.stdout.write(self.style.SUCCESS(f"✔ Reset {vouchers_updated} vouchers to DRAFT"))

        # ---------------------------------------------------
        # 2️⃣ Delete Replenishments
        # ---------------------------------------------------
        replenishments_deleted, _ = Replenishment.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"✔ Deleted {replenishments_deleted} replenishment records"))

        # ---------------------------------------------------
        # 3️⃣ Delete Ledger Entries
        # ---------------------------------------------------
        ledger_deleted, _ = LedgerEntry.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"✔ Deleted {ledger_deleted} ledger entries"))

        # ---------------------------------------------------
        # 4️⃣ Reset Fund Balances
        # ---------------------------------------------------
        funds = PettyCashFund.objects.all()
        for fund in funds:
            fund.current_balance = fund.fund_amount
            fund.save(update_fields=["current_balance"])

        self.stdout.write(self.style.SUCCESS("✔ Fund balances restored to initial amount"))

        # ---------------------------------------------------
        # 5️⃣ Delete Audit Logs
        # ---------------------------------------------------
        audit_deleted, _ = AuditLog.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"✔ Deleted {audit_deleted} audit logs"))

        # ---------------------------------------------------
        # 6️⃣ Delete Notifications
        # ---------------------------------------------------
        notifications_deleted, _ = Notification.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"✔ Deleted {notifications_deleted} notifications"))

        self.stdout.write(self.style.SUCCESS("🎉 Petty Cash DEV Reset Completed Successfully"))