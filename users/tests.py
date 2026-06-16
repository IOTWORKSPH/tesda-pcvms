from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from finance.models import FundCluster, PettyCashFund, ResponsibilityCenter
from pettycash.models import ExpenseCategory, PettyCashVoucher, TransactionType, VoucherStatus
from users.models import Entity, User


class CustodianDashboardTests(TestCase):
    def setUp(self):
        self.entity = Entity.objects.create(
            code="PTCZS",
            name="Provincial Training Center - Zamboanga Sibugay",
            address="Ipil, Zamboanga Sibugay",
        )
        self.custodian = User.objects.create_user(
            username="custodian",
            password="password",
            employee_number="EMP-001",
            first_name="Ronald",
            last_name="Alvarez",
            entity=self.entity,
        )
        self.requester = User.objects.create_user(
            username="requester",
            password="password",
            employee_number="EMP-002",
            first_name="Richard",
            last_name="Enot",
            entity=self.entity,
        )
        custodian_group = Group.objects.create(name="Custodian")
        self.custodian.groups.add(custodian_group)

        self.fund_cluster = FundCluster.objects.create(
            code="102",
            description="Regular Agency Fund",
        )
        self.responsibility_center = ResponsibilityCenter.objects.create(
            entity=self.entity,
            fund_cluster=self.fund_cluster,
            code="RC-001",
            description="Responsibility Center",
        )
        self.fund = PettyCashFund.objects.create(
            entity=self.entity,
            fund_cluster=self.fund_cluster,
            responsibility_center=self.responsibility_center,
            name="Petty Cash Fund",
            custodian=self.custodian,
            fund_amount=Decimal("15000.00"),
            current_balance=Decimal("15000.00"),
        )
        self.expense_category = ExpenseCategory.objects.create(
            entity=self.entity,
            code="50203010",
            name="Other Maintenance and Operating Expenses",
        )

    def test_action_queue_shows_print_links_for_other_requesters_approved_voucher(self):
        voucher = PettyCashVoucher.objects.create(
            entity=self.entity,
            fund=self.fund,
            pcv_no="PCV-2026-06-0015",
            requester=self.requester,
            transaction_type=TransactionType.CASH_ADVANCE,
            purpose="To refill LPG content",
            expense_category=self.expense_category,
            amount_requested=Decimal("400.00"),
            status=VoucherStatus.APPROVED,
            has_cnrr=True,
        )
        PettyCashVoucher.objects.create(
            entity=self.entity,
            fund=self.fund,
            pcv_no="PCV-2026-06-0016",
            requester=self.requester,
            transaction_type=TransactionType.REIMBURSEMENT,
            purpose="Meals during inspection",
            expense_category=self.expense_category,
            amount_requested=Decimal("275.00"),
            status=VoucherStatus.APPROVED,
        )

        self.client.force_login(self.custodian)
        response = self.client.get(reverse("users:dashboard_custodian"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Amount needed refund")
        self.assertContains(response, "275.00")
        self.assertContains(response, "PCV-2026-06-0015")
        self.assertContains(response, reverse("pettycash:print_pcv", args=[voucher.uuid]))
        self.assertContains(response, reverse("pettycash:print_pr", args=[voucher.uuid]))
        self.assertContains(response, reverse("pettycash:print_iar", args=[voucher.uuid]))
        self.assertContains(response, reverse("pettycash:print_cnrr", args=[voucher.uuid]))
        self.assertContains(response, reverse("pettycash:print_all", args=[voucher.uuid]))
