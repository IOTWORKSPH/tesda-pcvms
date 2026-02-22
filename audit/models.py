
#audit models.py codes
from django.db import models
from core.models import TimeStampedModel
from finance.models import FundCluster


class AuditAction(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    STATUS_CHANGE = "STATUS_CHANGE", "Status Change"
    APPROVAL = "APPROVAL", "Approval"
    RELEASE = "RELEASE", "Release Cash"
    LIQUIDATION = "LIQUIDATION", "Liquidation"
    POSTING = "POSTING", "Ledger Posting"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"
    CANCEL = "CANCEL", "Cancel"


class AuditLog(TimeStampedModel):

    entity = models.ForeignKey(
        "users.Entity",
        on_delete=models.PROTECT
    )

    user = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT
    )

    action = models.CharField(
        max_length=30,
        choices=AuditAction.choices
    )

    model_name = models.CharField(max_length=100)

    object_id = models.CharField(max_length=50)

    description = models.TextField(blank=True)

    previous_status = models.CharField(
        max_length=30,
        blank=True
    )

    new_status = models.CharField(
        max_length=30,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} - {self.model_name} - {self.object_id}"
