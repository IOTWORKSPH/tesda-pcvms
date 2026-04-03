# pettycash/services/excel/replenishment_excel.py

from openpyxl import Workbook
from django.http import HttpResponse

from .excel_styles import get_styles
from .appendix_49_excel import generate_appendix_49
from .appendix_50_excel import generate_appendix_50
from .appendix_51_excel import generate_appendix_51
from .summary_excel import generate_summary


def generate_replenishment_excel(context):
    wb = Workbook()
    styles = get_styles()

    generate_appendix_49(wb, context, styles)
    generate_appendix_50(wb, context, styles)
    generate_appendix_51(wb, context, styles)
    generate_summary(wb, context, styles)

    report_number = context.get("report_number")
    filename = (
        f"replenishment_{report_number}.xlsx"
        if report_number
        else "replenishment_package.xlsx"
    )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response