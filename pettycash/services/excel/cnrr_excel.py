# pettycash/services/excel/cnrr_excel.py

from openpyxl import load_workbook
from django.conf import settings
import os


def generate_cnrr_excel(voucher, administrator):

    template_path = os.path.join(
        settings.BASE_DIR,
        "pettycash",
        "templates",
        "excel_templates",
        "CNRR_template.xlsx"
    )

    wb = load_workbook(template_path)
    ws = wb.active

    entity = voucher.entity

    # ================= HEADER =================
    fullname = voucher.requester.get_full_name().upper()

    ws["C5"] = fullname
    ws["N5"] = fullname

    ws["A6"] = entity.name
    ws["L6"] = entity.name

    # ================= PARTICULARS =================
    category = voucher.expense_category.name if voucher.expense_category else ""

    ws["A9"] = category
    ws["L9"] = category

    amount = float(voucher.amount_liquidated or voucher.amount_requested or 0)

    ws["I9"] = amount
    ws["T9"] = amount

    ws["I18"] = amount
    ws["T18"] = amount

    # ================= PURPOSE =================
    ws["C19"] = voucher.purpose
    ws["N19"] = voucher.purpose

    # ================= SIGNATORIES =================
    ws["C23"] = fullname
    ws["N23"] = fullname

    if administrator:
        admin_name = administrator.get_full_name().upper()
        ws["H23"] = admin_name
        ws["S23"] = admin_name

    # ================= DATE =================
    if voucher.purchase_date:
        date_str = voucher.purchase_date.strftime("%B %d, %Y")

        ws["D24"] = date_str
        ws["I24"] = date_str
        ws["O24"] = date_str
        ws["T24"] = date_str

    return wb