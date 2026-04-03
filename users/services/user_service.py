# users/services/user_service.py

from django.db import transaction
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from audit.services.audit_service import AuditService
from audit.models import AuditAction

from .email_service import EmailService

User = get_user_model()


class UserService:
    """
    Enterprise User Management Service
    -----------------------------------
    • Handles user creation
    • Assigns groups
    • Enforces entity isolation
    • Sends secure onboarding email
    • Audit compliant
    """

    # ==========================================================
    # SYSTEM ADMIN: CREATE ENTITY ADMINISTRATOR
    # ==========================================================

    @staticmethod
    @transaction.atomic
    def create_administrator(entity, form_data, created_by):

        user = User.objects.create(
            username=form_data["username"],
            email=form_data["email"],
            first_name=form_data["first_name"],
            last_name=form_data["last_name"],
            employee_number=form_data["employee_number"],
            position=form_data.get("position", ""),
            designation=form_data.get("designation", ""),
            office=form_data.get("office", ""),
            entity=entity,
            is_active=True,
        )

        # Prevent login until password set
        user.set_unusable_password()
        user.save()

        # Assign Administrator group
        admin_group, _ = Group.objects.get_or_create(name="Administrator")
        user.groups.add(admin_group)

        # Send onboarding email
        EmailService.send_password_setup_email(user)

        # Audit
        AuditService.log(
            entity=entity,
            user=created_by,
            action=AuditAction.CREATE,
            model_name="User",
            object_id=user.username,
            description="Administrator account created",
        )

        return user

    # ==========================================================
    # ENTITY ADMIN: CREATE USER WITH ROLE
    # ==========================================================

    @staticmethod
    @transaction.atomic
    def create_entity_user(entity, form_data, created_by):

        role = form_data["role"]

        # SECURITY: Prevent creating Administrator from here
        if role == "Administrator":
            raise PermissionError("Cannot assign Administrator role.")

        user = User.objects.create(
            username=form_data["username"],
            email=form_data["email"],
            first_name=form_data["first_name"],
            last_name=form_data["last_name"],
            employee_number=form_data["employee_number"],
            position=form_data.get("position", ""),
            designation=form_data.get("designation", ""),
            office=form_data.get("office", ""),
            entity=entity,
            is_active=True,
        )

        user.set_unusable_password()
        user.save()

        # Assign group
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        # Send onboarding email
        EmailService.send_password_setup_email(user)

        # Audit
        AuditService.log(
            entity=entity,
            user=created_by,
            action=AuditAction.CREATE,
            model_name="User",
            object_id=user.username,
            description=f"User created with role {role}",
        )

        return user