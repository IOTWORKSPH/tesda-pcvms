# pettycash/services/excel/appendix_51_excel.py

from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter


def generate_appendix_51(wb, context, styles):

    fund = context["fund"]
    register_rows = context["register_rows"]
    expense_categories = context["expense_categories"]
    category_totals = context["category_totals"]
    total = context["total"]
    generated_date = context["generated_date"]

    ws = wb.create_sheet("Appendix 51")

    bold = styles["bold"]
    bold_large = styles["bold_large"]
    center = styles["center"]
    right = styles["right"]
    wrap = styles["wrap"]
    border = styles["border"]

    row = 1

    total_columns = 6 + len(expense_categories)

    # =====================================================
    # APPENDIX LABEL
    # =====================================================
    ws.merge_cells(start_row=row, start_column=1,
                   end_row=row, end_column=total_columns)
    ws.cell(row=row, column=1).value = "Appendix 51"
    ws.cell(row=row, column=1).alignment = Alignment(horizontal="right")
    row += 1

    # =====================================================
    # TITLE
    # =====================================================
    ws.merge_cells(start_row=row, start_column=1,
                   end_row=row, end_column=total_columns)
    ws.cell(row=row, column=1).value = "PETTY CASH FUND REGISTER"
    ws.cell(row=row, column=1).font = bold_large
    ws.cell(row=row, column=1).alignment = center
    row += 2

    # =====================================================
    # HEADER INFO
    # =====================================================
    ws.cell(row=row, column=1).value = "Department/Agency:"
    ws.cell(row=row, column=1).font = bold
    ws.cell(row=row, column=2).value = "TESDA"

    ws.cell(row=row, column=5).value = "Petty Cash Fund Custodian:"
    ws.cell(row=row, column=5).font = bold
    ws.cell(row=row, column=6).value = fund.custodian.get_full_name()
    row += 1

    ws.cell(row=row, column=1).value = "Sub-Office/District/Division:"
    ws.cell(row=row, column=1).font = bold
    ws.cell(row=row, column=2).value = fund.entity.name

    ws.cell(row=row, column=5).value = "Fund Cluster:"
    ws.cell(row=row, column=5).font = bold
    ws.cell(row=row, column=6).value = fund.fund_cluster.code
    row += 1

    ws.cell(row=row, column=1).value = "Municipality/City/Province:"
    ws.cell(row=row, column=1).font = bold
    ws.cell(row=row, column=2).value = fund.entity.address or "-"

    ws.cell(row=row, column=5).value = "Sheet No:"
    ws.cell(row=row, column=5).font = bold
    ws.cell(row=row, column=6).value = 1
    row += 2

    # =====================================================
    # COMPLEX HEADER (3 ROWS)
    # =====================================================

    header_start = row

    # Row 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row+2, end_column=1)
    ws.cell(row=row, column=1).value = "Date"

    ws.merge_cells(start_row=row, start_column=2, end_row=row+2, end_column=2)
    ws.cell(row=row, column=2).value = "PCV / Check No."

    ws.merge_cells(start_row=row, start_column=3, end_row=row+2, end_column=3)
    ws.cell(row=row, column=3).value = "Particulars"

    ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=6)
    ws.cell(row=row, column=4).value = "PETTY CASH FUND"

    breakdown_start = 7
    breakdown_end = total_columns

    ws.merge_cells(start_row=row, start_column=breakdown_start,
                   end_row=row, end_column=breakdown_end)
    ws.cell(row=row, column=breakdown_start).value = "BREAKDOWN OF PAYMENTS"

    row += 1

    # Row 2
    ws.cell(row=row, column=4).value = "Receipts"
    ws.cell(row=row, column=5).value = "Payments"
    ws.cell(row=row, column=6).value = "Balance"

    col = 7
    for category in expense_categories:
        ws.cell(row=row, column=col).value = category.name
        ws.cell(row=row, column=col).alignment = wrap
        col += 1

    row += 1

    # Row 3
    ws.cell(row=row, column=4).value = "( + )"
    ws.cell(row=row, column=5).value = "( - )"

    # Style all header rows
    for r in range(header_start, header_start + 3):
        ws.row_dimensions[r].height = 35  # increase height for clean look
        for c in range(1, total_columns + 1):
            ws.cell(row=r, column=c).font = bold
            ws.cell(row=r, column=c).alignment = center
            ws.cell(row=r, column=c).border = border

    row += 1

    # =====================================================
    # DATA ROWS
    # =====================================================

    for entry in register_rows:

        ws.cell(row=row, column=1).value = entry["date"].strftime("%B %d, %Y")
        ws.cell(row=row, column=2).value = entry["reference"]

        ws.cell(row=row, column=3).value = entry["particulars"]
        ws.cell(row=row, column=3).alignment = wrap

        ws.cell(row=row, column=4).value = entry["receipt"] or ""
        ws.cell(row=row, column=5).value = entry["payment"] or ""
        ws.cell(row=row, column=6).value = entry["balance"] or ""

        ws.cell(row=row, column=4).alignment = right
        ws.cell(row=row, column=5).alignment = right
        ws.cell(row=row, column=6).alignment = right

        col = 7
        for category in expense_categories:
            amount = entry["breakdown"].get(category.id)
            ws.cell(row=row, column=col).value = amount or ""
            ws.cell(row=row, column=col).alignment = right
            col += 1

        for c in range(1, total_columns + 1):
            ws.cell(row=row, column=c).border = border

        ws.row_dimensions[row].height = None
        row += 1

    # =====================================================
    # TOTAL ROW
    # =====================================================

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
    ws.cell(row=row, column=1).value = "TOTAL"
    ws.cell(row=row, column=1).font = bold
    ws.cell(row=row, column=1).alignment = right

    ws.cell(row=row, column=5).value = total
    ws.cell(row=row, column=5).font = bold
    ws.cell(row=row, column=5).alignment = right

    col = 7
    for category in expense_categories:
        ws.cell(row=row, column=col).value = category_totals.get(category.id, 0)
        ws.cell(row=row, column=col).font = bold
        ws.cell(row=row, column=col).alignment = right
        col += 1

    for c in range(1, total_columns + 1):
        ws.cell(row=row, column=c).border = border

    row += 4

    # =====================================================
    # SIGNATURE
    # =====================================================

    ws.merge_cells(start_row=row, start_column=3,
                   end_row=row, end_column=total_columns - 2)
    ws.cell(row=row, column=3).value = fund.custodian.get_full_name().upper()
    ws.cell(row=row, column=3).font = bold
    ws.cell(row=row, column=3).alignment = center
    row += 1

    ws.merge_cells(start_row=row, start_column=3,
                   end_row=row, end_column=total_columns - 2)
    ws.cell(row=row, column=3).value = "(Signature over Printed)"
    ws.cell(row=row, column=3).alignment = center
    row += 1

    ws.merge_cells(start_row=row, start_column=3,
                   end_row=row, end_column=total_columns - 2)
    ws.cell(row=row, column=3).value = "Name Petty Cash Fund Custodian"
    ws.cell(row=row, column=3).alignment = center
    row += 1

    ws.merge_cells(start_row=row, start_column=3,
                   end_row=row, end_column=total_columns - 2)
    ws.cell(row=row, column=3).value = generated_date.strftime("%B %d, %Y")
    ws.cell(row=row, column=3).alignment = center

    # =====================================================
    # COLUMN WIDTHS (VERY IMPORTANT FOR CLEAN LOOK)
    # =====================================================

    ws.column_dimensions["A"].width = 15
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 28
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 12
    ws.column_dimensions["F"].width = 12

    col = 7
    for _ in expense_categories:
        column_letter = get_column_letter(col)
        ws.column_dimensions[column_letter].width = 16
        col += 1

    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.fitToWidth = 1