
#numbering_service.py codes
from django.db import transaction
from django.db.models import Max
from datetime import datetime

from pettycash.models import PettyCashVoucher


class DocumentNumberService:

    @staticmethod
    @transaction.atomic
    def generate(entity, doc_type):
        """
        doc_type: 'PCV', 'PR', 'IAR'
        """

        year = datetime.now().year

        field_map = {
            "PCV": "pcv_no",
            "PR": "pr_no",
            "IAR": "iar_no",
        }

        field_name = field_map.get(doc_type)

        if not field_name:
            raise ValueError("Invalid document type")

        # Lock rows for safe increment
        last_doc = (
            PettyCashVoucher.objects
            .select_for_update()
            .filter(
                entity=entity,
                **{
                    f"{field_name}__startswith": f"{doc_type}-{year}-"
                }
            )
            .order_by(f"-{field_name}")
            .first()
        )

        if last_doc and getattr(last_doc, field_name):
            last_series = int(
                getattr(last_doc, field_name).split("-")[-1]
            )
            new_series = last_series + 1
        else:
            new_series = 1

        return f"{doc_type}-{year}-{new_series:04d}"
