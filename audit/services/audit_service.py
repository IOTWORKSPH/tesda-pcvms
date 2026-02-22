
#Audit/Services/audit_service.py codes
from audit.models import AuditLog


class AuditService:
    """
    Centralized audit logging.
    """

    @staticmethod
    def log(entity, user, action, model_name, object_id,
            description="", previous_status="", new_status=""):

        AuditLog.objects.create(
            entity=entity,
            user=user,
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            description=description,
            previous_status=previous_status,
            new_status=new_status,
        )


