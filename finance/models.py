
#finance models.py codes
from django.db import models
from django.db.models import Q
from decimal import Decimal
from core.models import TimeStampedModel


# ==========================================================
# FUND CLUSTER (COA Classification)
# ==========================================================

class FundCluster(models.Model):
    """
    Government Fund Cluster (e.g., 101, 102, 151)
    """

    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.description}"


# ==========================================================
# RESPONSIBILITY CENTER
# ==========================================================

class ResponsibilityCenter(models.Model):
    """
    Government Responsibility Center Code (RCC)
    """

    entity = models.ForeignKey(
        "users.Entity",
        on_delete=models.PROTECT,
        related_name="responsibility_centers"
    )

    fund_cluster = models.ForeignKey(
        FundCluster,
        on_delete=models.PROTECT,
        related_name="responsibility_centers"
    )

    code = models.CharField(max_length=50)
    description = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("entity", "code")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.description}"


# ==========================================================
# REFERENCE TYPES
# ==========================================================

class ReferenceType(models.TextChoices):
    PCV = "PCV", "Petty Cash Voucher"
    REPLENISHMENT = "REPLENISHMENT", "Replenishment"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"
    REVERSAL = "REVERSAL", "Reversal"


# ==========================================================
# PETTY CASH FUND (Imprest System)
# ==========================================================

class PettyCashFund(TimeStampedModel):

    entity = models.ForeignKey(
        "users.Entity",
        on_delete=models.PROTECT,
        related_name="funds"
    )

    fund_cluster = models.ForeignKey(
        FundCluster,
        on_delete=models.PROTECT,
        related_name="funds"
    )

    responsibility_center = models.ForeignKey(
        ResponsibilityCenter,
        on_delete=models.PROTECT,
        related_name="funds"
    )

    name = models.CharField(max_length=100)

    custodian = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="custodian_funds"
    )

    fund_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    current_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00")
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("entity", "name")
        ordering = ["entity", "name"]

    def __str__(self):
        return f"{self.entity.code} - {self.name}"

    def clean(self):
        if self.current_balance < 0:
            raise ValueError("Fund balance cannot be negative.")

    @property
    def is_depleted(self):
        return self.current_balance <= 0


# ==========================================================
# LEDGER ENTRY
# ==========================================================

class LedgerEntry(TimeStampedModel):

    fund = models.ForeignKey(
        PettyCashFund,
        on_delete=models.PROTECT,
        related_name="ledger_entries"
    )

    transaction_date = models.DateField()

    debit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00")
    )

    credit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00")
    )

    running_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    reference_type = models.CharField(
        max_length=20,
        choices=ReferenceType.choices
    )

    reference_no = models.CharField(
        max_length=50
    )

    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT
    )

    is_reversal = models.BooleanField(default=False)

    reversed_entry = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reversal_of"
    )

    class Meta:
        ordering = ["transaction_date", "id"]

        constraints = [

            #
            models.CheckConstraint(
                condition=(
                    (Q(debit__gt=0) & Q(credit=0)) |
                    (Q(credit__gt=0) & Q(debit=0))
                ),
                name="valid_debit_or_credit"
            ),

            # Prevent duplicate document posting per fund
            models.UniqueConstraint(
                fields=["fund", "reference_type", "reference_no"],
                name="unique_reference_posting_per_fund"
            ),
        ]

    def __str__(self):
        return f"{self.reference_no} ({self.reference_type})"

    def clean(self):

        if self.debit <= 0 and self.credit <= 0:
            raise ValueError("Either debit or credit must be greater than zero.")

        if self.debit > 0 and self.credit > 0:
            raise ValueError("Cannot have both debit and credit.")

        if self.running_balance < 0:
            raise ValueError("Running balance cannot be negative.")
