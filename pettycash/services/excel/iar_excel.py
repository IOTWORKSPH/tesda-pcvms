from openpyxl import load_workbook
from django.conf import settings
import os
from users.models import User


def generate_iar_excel(voucher):

    # =====================================================
    # LOAD TEMPLATE
    # =====================================================
    template_path = os.path.join(
        settings.BASE_DIR,
        "pettycash",
        "templates",
        "excel_templates",
        "IAR_template.xlsx"
    )

    wb = load_workbook(template_path)
    ws = wb.active

    entity = voucher.entity

    # =====================================================
    # HEADER
    # =====================================================

    # Entity Name
    ws["B5"] = entity.name

    # Fund Cluster (you said fixed = 102)
    ws["E5"] = "102"

    # Supplier
    ws["B7"] = voucher.supplier.name if voucher.supplier else ""

    # IAR Number (leave blank series format)
    if voucher.purchase_date:
        ws["E7"] = f"{voucher.purchase_date.strftime('%Y-%m')}-_____"
    else:
        ws["E7"] = "_____"

    # Invoice Number
    ws["E9"] = voucher.official_receipt_number or ""

    # Date Purchased
    if voucher.purchase_date:
        ws["E10"] = voucher.purchase_date.strftime("%B %d, %Y")

    # =====================================================
    # ITEMS TABLE
    # =====================================================

    start_row = 13

    for i, item in enumerate(voucher.items.all(), start=0):
        row = start_row + i

        ws[f"A{row}"] = i + 1  # Series Number
        ws[f"B{row}"] = item.description
        ws[f"D{row}"] = item.unit
        ws[f"E{row}"] = float(item.quantity)

    # =====================================================
    # DATES (BOTTOM)
    # =====================================================

    if voucher.purchase_date:
        formatted_date = voucher.purchase_date.strftime("%B %d, %Y")

        ws["B23"] = formatted_date
        ws["D23"] = formatted_date

    # =====================================================
    # INSPECTION TEAM (GROUP: Inspection)
    # =====================================================

    inspectors = User.objects.filter(
        entity=entity,
        groups__name="Inspection",
        is_active=True
    )

    inspector_list = list(inspectors)

    # First Inspector
    if len(inspector_list) >= 1:
        ws["A30"] = inspector_list[0].get_full_name().upper()
        ws["A31"] = getattr(inspector_list[0], "position", "")

    # Second Inspector
    if len(inspector_list) >= 2:
        ws["A34"] = inspector_list[1].get_full_name().upper()
        ws["A35"] = getattr(inspector_list[1], "position", "")

    # =====================================================
    # SUPPLY OFFICER (GROUP: Supply)
    # =====================================================

    supply = User.objects.filter(
        entity=entity,
        groups__name="Supply",
        is_active=True
    ).first()

    if supply:
        ws["C30"] = supply.get_full_name().upper()

    return wb