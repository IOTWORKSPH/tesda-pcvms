from datetime import datetime
from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.utils import timezone

from finance.models import FundCluster, PettyCashFund, ResponsibilityCenter
from pettycash.models import Replenishment, ReplenishmentStatus
from pettycash.services.replenishment_builder import build_replenishment_context
from users.models import Entity, User


class ReplenishmentContextTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.entity = Entity.objects.create(
            code="PTCZS",
            name="Provincial Training Center - Zamboanga Sibugay",
            address="Ipil, Zamboanga Sibugay",
        )
        self.user = User.objects.create_user(
            username="custodian",
            password="password",
            employee_number="EMP-001",
            first_name="Ronald",
            last_name="Alvarez",
            entity=self.entity,
        )
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
            custodian=self.user,
            fund_amount=Decimal("15000.00"),
            current_balance=Decimal("1043.85"),
        )

    def _create_replenishment(self, report_number, series_number, created_at, **kwargs):
        replenishment = Replenishment.objects.create(
            fund=self.fund,
            year=2026,
            series_number=series_number,
            report_number=report_number,
            opening_balance=kwargs.get("opening_balance", Decimal("15000.00")),
            total_expenses=kwargs.get("total_expenses", Decimal("100.00")),
            period_start=kwargs.get("period_start"),
            period_end=kwargs.get("period_end"),
            check_number=kwargs.get("check_number", ""),
            check_date=kwargs.get("check_date"),
            check_amount=kwargs.get("check_amount", Decimal("0.00")),
            cash_on_hand=kwargs.get("cash_on_hand", Decimal("0.00")),
            status=kwargs.get("status", ReplenishmentStatus.DRAFT),
            created_by=self.user,
        )
        Replenishment.objects.filter(pk=replenishment.pk).update(created_at=created_at)
        return Replenishment.objects.get(pk=replenishment.pk)

    def test_appendix_50_opening_rows_use_previous_report_and_check_dates(self):
        previous_created_at = timezone.make_aware(datetime(2026, 4, 22, 8, 0))
        current_created_at = timezone.make_aware(datetime(2026, 5, 18, 10, 30))
        previous_check_date = timezone.datetime(2026, 4, 30).date()

        previous_replenishment = self._create_replenishment(
            "2026-0001",
            1,
            previous_created_at,
            total_expenses=Decimal("14828.00"),
            check_number="1608352",
            check_date=previous_check_date,
            check_amount=Decimal("14828.00"),
            status=ReplenishmentStatus.RELEASED,
        )
        current_replenishment = self._create_replenishment(
            "2026-0002",
            2,
            current_created_at,
            total_expenses=Decimal("13956.15"),
            status=ReplenishmentStatus.DRAFT,
        )

        request = self.factory.post(
            "/pettycash/reports/replenishment/package/",
            {"replenishment_id": str(current_replenishment.pk)},
        )
        request.user = self.user

        context = build_replenishment_context(request)
        cash_on_hand_row = context["records"][0]
        replenishment_row = context["records"][1]

        self.assertEqual(cash_on_hand_row["particulars"], "Cash on Hand")
        self.assertEqual(
            cash_on_hand_row["date"],
            timezone.localtime(previous_replenishment.created_at).date(),
        )
        self.assertEqual(replenishment_row["particulars"], "Replenishment")
        self.assertEqual(replenishment_row["reference"], "1608352")
        self.assertEqual(replenishment_row["date"], previous_check_date)
