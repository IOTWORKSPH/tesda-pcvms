
#Pettycash Models.py Codes

import uuid
from decimal import Decimal

from django.db import models
from django.db.models import Q, F, Sum, DecimalField, ExpressionWrapper
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from core.models import TimeStampedModel


# ==========================================================
# SUPPLIER
# ==========================================================

class Supplier(TimeStampedModel):

    entity = models.ForeignKey(
        "users.Entity",
        on_delete=models.PROTECT,
        related_name="suppliers"
    )

    name = models.CharField(max_length=255)
    tin = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("entity", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


# ==========================================================
# EXPENSE CATEGORY
# ==========================================================

class ExpenseCategory(TimeStampedModel):

    entity = models.ForeignKey(
        "users.Entity",
        on_delete=models.PROTECT,
        related_name="expense_categories"
    )

    code = models.CharField(max_length=50)
    name = models.CharField(max_length=150)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("entity", "code")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"



class TransactionType(models.TextChoices):
    REIMBURSEMENT = "REIMBURSEMENT", "Reimbursement"
    CASH_ADVANCE = "CASH_ADVANCE", "Cash Advance"


class VoucherStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    FOR_APPROVAL = "FOR_APPROVAL", "For Approval"
    APPROVED = "APPROVED", "Approved"
    RELEASED = "RELEASED", "Cash Released"
    LIQUIDATED = "LIQUIDATED", "Liquidated"
    POSTED = "POSTED", "Posted to Ledger"
    CANCELLED = "CANCELLED", "Cancelled"


class PettyCashVoucher(TimeStampedModel):

    # =========================================================
    # IDENTIFICATION
    # =========================================================

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    entity = models.ForeignKey(
        "users.Entity",
        on_delete=models.PROTECT
    )

    fund = models.ForeignKey(
        "finance.PettyCashFund",
        on_delete=models.PROTECT
    )

    replenishment = models.ForeignKey(
        "Replenishment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vouchers"
    )

    pcv_no = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    pr_no = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    iar_no = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    # =========================================================
    # TRANSACTION INFO
    # =========================================================

    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices
    )

    requester = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="requested_vouchers"
    )

    purpose = models.TextField()

    expense_category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT
    )

    amount_requested = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )

    # =========================================================
    # RELEASE INFO (Cash Advance)
    # =========================================================

    release_date = models.DateTimeField(null=True, blank=True)

    released_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="released_vouchers"
    )

    # =========================================================
    # PURCHASE INFO
    # =========================================================

    purchase_date = models.DateField(null=True, blank=True)

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    official_receipt_number = models.CharField(
        max_length=100,
        blank=True
    )

    # =========================================================
    # LIQUIDATION
    # =========================================================

    amount_liquidated = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    # =========================================================
    # STATUS
    # =========================================================

    status = models.CharField(
        max_length=20,
        choices=VoucherStatus.choices,
        default=VoucherStatus.DRAFT
    )

    is_posted_to_ledger = models.BooleanField(default=False)
    is_release_posted = models.BooleanField(default=False)
    is_liquidation_posted = models.BooleanField(default=False)
    is_replenished = models.BooleanField(default=False)
    has_cnrr = models.BooleanField(default=False)

    # =========================================================
    # META
    # =========================================================

    class Meta:
        ordering = ["-created_at"]

        constraints = [

            models.UniqueConstraint(
                fields=["entity", "pcv_no"],
                condition=Q(pcv_no__isnull=False),
                name="unique_pcv_no_per_entity"
            ),

            models.CheckConstraint(
                condition=(
                    Q(is_replenished=False) |
                    Q(replenishment__isnull=False)
                ),
                name="replenished_must_have_replenishment"
            ),

            models.CheckConstraint(
                condition=(
                    Q(is_replenished=False) |
                    Q(status=VoucherStatus.POSTED)
                ),
                name="replenished_must_be_posted"
            ),

            models.CheckConstraint(
                condition=(
                    Q(status=VoucherStatus.POSTED, is_posted_to_ledger=True) |
                    ~Q(status=VoucherStatus.POSTED)
                ),
                name="posted_status_requires_flag"
            ),
        ]

    # =========================================================
    # MODEL VALIDATION
    # =========================================================

    def clean(self):

        if self.is_replenished and not self.replenishment:
            raise ValidationError(
                "Replenished voucher must have replenishment record."
            )

        if self.status == VoucherStatus.POSTED and not self.is_posted_to_ledger:
            raise ValidationError(
                "Posted voucher must have ledger posting flag."
            )

    # =========================================================
    # STRING REPRESENTATION
    # =========================================================

    def __str__(self):
        return self.pcv_no or str(self.uuid)

    # =========================================================
    # COMPUTED PROPERTIES
    # =========================================================

    @property
    def total_items_amount(self):
        total = self.items.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("quantity") * F("unit_cost"),
                    output_field=DecimalField(
                        max_digits=14,
                        decimal_places=2
                    )
                )
            )
        )["total"]

        return total or Decimal("0.00")

    @property
    def is_fully_liquidated(self):
        if self.transaction_type != TransactionType.CASH_ADVANCE:
            return True
        return self.status in [
            VoucherStatus.LIQUIDATED,
            VoucherStatus.POSTED
        ]

    @property
    def variance_amount(self):
        if self.transaction_type != TransactionType.CASH_ADVANCE:
            return Decimal("0.00")

        if self.status not in [
            VoucherStatus.LIQUIDATED,
            VoucherStatus.POSTED
        ]:
            return Decimal("0.00")

        requested = self.amount_requested or Decimal("0.00")
        actual = self.amount_liquidated or Decimal("0.00")

        return requested - actual

    @property
    def variance_type(self):
        diff = self.variance_amount

        if diff > 0:
            return "EXCESS"
        elif diff < 0:
            return "SHORTAGE"
        return "NONE"

    @property
    def variance_display(self):
        return abs(self.variance_amount)

    @property
    def has_receipt(self):
        return self.receipts.exists()

    @property
    def actual_amount(self):
        """
        Returns the TRUE expense amount for reporting.
        - Cash Advance:
            • If liquidated → use liquidated amount
            • If not yet liquidated → use requested amount
        - Reimbursement → use requested amount
        """
        if self.transaction_type == TransactionType.CASH_ADVANCE:
            if self.status in [VoucherStatus.LIQUIDATED, VoucherStatus.POSTED]:
                return self.amount_liquidated or Decimal("0.00")
            return self.amount_requested or Decimal("0.00")

        return self.amount_requested or Decimal("0.00")


# ==========================================================
# LIQUIDATION REVIEW HISTORY
# ==========================================================

class LiquidationReview(models.Model):

    voucher = models.ForeignKey(
        "PettyCashVoucher",
        on_delete=models.CASCADE,
        related_name="liquidation_reviews"
    )

    reviewed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    remarks = models.TextField()

    action = models.CharField(
        max_length=20,
        choices=[
            ("RETURNED", "Returned to Staff"),
            ("APPROVED", "Approved by Custodian"),
        ]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.voucher.pcv_no} - {self.action}"
    

class PCVItem(TimeStampedModel):

    voucher = models.ForeignKey(
        PettyCashVoucher,
        on_delete=models.CASCADE,
        related_name="items"
    )

    description = models.CharField(max_length=255)

    unit = models.CharField(
        max_length=50,
        help_text="Unit of measurement (e.g., pcs, box, liter, kg, meter)"
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    @property
    def total_cost(self):
        return self.quantity * self.unit_cost


class ReceiptAttachment(TimeStampedModel):

    voucher = models.ForeignKey(
        PettyCashVoucher,
        on_delete=models.CASCADE,
        related_name="receipts"
    )

    file = models.FileField(upload_to="receipts/%Y/%m/")
    uploaded_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT
    )


class PCVApproval(TimeStampedModel):

    voucher = models.ForeignKey(
        PettyCashVoucher,
        on_delete=models.CASCADE,
        related_name="approvals"
    )

    approved_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT
    )

    role = models.CharField(max_length=100)
    remarks = models.TextField(blank=True)


class Notification(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    voucher = models.ForeignKey(PettyCashVoucher, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)



class ReplenishmentStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED_TO_ACCOUNTING = "SUBMITTED_TO_ACCOUNTING", "Submitted to Accounting"
    RELEASED = "RELEASED", "Released"

class Replenishment(TimeStampedModel):

    fund = models.ForeignKey(
        "finance.PettyCashFund",
        on_delete=models.PROTECT,
        related_name="replenishments"
    )

    # Report Control
    year = models.IntegerField()
    series_number = models.IntegerField()
    report_number = models.CharField(max_length=30, unique=True)
    sheet_number = models.IntegerField(default=1)

    # Snapshot at time of report generation
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2)
    total_expenses = models.DecimalField(max_digits=14, decimal_places=2)

    # Period covered
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    # Check Information (filled only when released)
    check_number = models.CharField(max_length=50, blank=True)
    check_date = models.DateField(null=True, blank=True)
    check_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Status Control
    status = models.CharField(
        max_length=30,
        choices=ReplenishmentStatus.choices,
        default=ReplenishmentStatus.DRAFT
    )
    cash_on_hand = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT
    )

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("fund", "year", "series_number")
        constraints = [
            models.CheckConstraint(
                condition=Q(cash_on_hand__gte=0),
                name="cash_on_hand_non_negative"
            )
        ]


    def calculate_total_expenses(self):
        total = Decimal("0.00")
        for voucher in self.vouchers.all():
            total += voucher.actual_amount
        return total

    def clean(self):
        if self.opening_balance is not None:
            if (self.cash_on_hand + self.total_expenses) != self.opening_balance:
                raise ValidationError(
                    "Imprest fund imbalance: "
                    "Cash on hand + total expenses must equal opening balance."
                )
        
    def __str__(self):
        return self.report_number