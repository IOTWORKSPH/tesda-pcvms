
#User Models.py codes

from django.contrib.auth.models import AbstractUser
from django.db import models


class Entity(models.Model):
    """
    Represents a Training Center / Office / Division
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique entity code (e.g., PTC-ZS)"
    )

    name = models.CharField(
        max_length=255,
        help_text="Official name of the entity"
    )

    address = models.TextField(blank=True)

    tin = models.CharField(
        max_length=100,
        blank=True,
        help_text="Tax Identification Number"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"
    

class User(AbstractUser):
    """
    Government-Grade Custom User Model
    Designed for Financial & Petty Cash Systems
    """

    # =============================
    # OFFICIAL EMPLOYEE INFORMATION
    # =============================
    entity = models.ForeignKey(
        Entity,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True
    )

    employee_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Government issued employee number"
    )

    position = models.CharField(
        max_length=150,
        blank=True,
        help_text="Official Position Title (e.g., Administrative Officer III)"
    )

    designation = models.CharField(
        max_length=150,
        blank=True,
        help_text="Functional designation (e.g., Supply Officer, Cashier)"
    )

    office = models.CharField(
        max_length=150,
        blank=True,
        help_text="Office / Division assignment"
    )

    # =============================
    # SYSTEM ROLE CONTROL
    # =============================

    is_system_admin = models.BooleanField(
        default=False,
        help_text="Has full system control across all modules"
    )

    # =============================
    # DIGITAL ASSETS (Future Ready)
    # =============================

    profile_image = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True
    )

    signature = models.ImageField(
        upload_to="signatures/",
        blank=True,
        null=True,
        help_text="Digital signature for official documents"
    )

    # =============================
    # ACCOUNT STATUS
    # =============================

    is_active_employee = models.BooleanField(
        default=True,
        help_text="Soft deactivate employee without deleting record"
    )

    # =============================
    # STRING REPRESENTATION
    # =============================

    def __str__(self):
        return f"{self.get_full_name()} ({self.employee_number})"

    # =============================
    # HELPER METHODS
    # =============================

    def has_role(self, role_name):
        """
        Check if user belongs to a specific Django Group
        """
        return self.groups.filter(name=role_name).exists()

    def get_roles(self):
        return self.groups.values_list("name", flat=True)


