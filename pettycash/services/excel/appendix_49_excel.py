# pettycash/services/excel/appendix_49_excel.py

from openpyxl.styles import Font, Alignment


def generate_appendix_49(wb, context, styles):

    fund = context["fund"]
    vouchers = context["vouchers"]
    total = context["total"]
    generated_date = context["generated_date"]

    date_from = context.get("date_from")
    date_to = context.get("date_to")
    period_start = context.get("period_start")
    period_end = context.get("period_end")

    report_number = context.get("report_number", "")
    sheet_number = context.get("sheet_number", 1)

    ws = wb.active
    ws.title = "Appendix 49"

    bold = styles["bold"]
    bold_large = styles["bold_large"]
    center = styles["center"]
    right = styles["right"]
    border = styles["border"]
    wrap = styles["wrap"]

    row = 1

    # =====================================================
    # APPENDIX LABEL (RIGHT)
    # =====================================================
    ws.merge_cells("A1:D1")
    ws["A1"] = "Appendix 49"
    ws["A1"].alignment = Alignment(horizontal="right")
    row += 1

    # =====================================================
    # TITLE
    # =====================================================
    ws.merge_cells(f"A{row}:D{row}")
    ws.cell(row=row, column=1).value = "REPORT ON PAID PETTY CASH VOUCHERS"
    ws.cell(row=row, column=1).font = bold_large
    ws.cell(row=row, column=1).alignment = center
    row += 1

    # =====================================================
    # PERIOD COVERED
    # =====================================================
    if date_from and date_to:
        period_text = f"{date_from.strftime('%B %d, %Y')} - {date_to.strftime('%B %d, %Y')}"
    elif period_start and period_end:
        period_text = f"{period_start.strftime('%B %d, %Y')} - {period_end.strftime('%B %d, %Y')}"
    else:
        period_text = "No Transactions Available"

    ws.merge_cells(f"A{row}:D{row}")
    ws.cell(row=row, column=1).value = f"Period Covered: {period_text}"
    ws.cell(row=row, column=1).alignment = center
    row += 2

    # =====================================================
    # ENTITY + REPORT INFO (2 COLUMNS)
    # =====================================================
    ws.cell(row=row, column=1).value = "Entity Name:"
    ws.cell(row=row, column=1).font = bold
    ws.cell(row=row, column=2).value = fund.entity.name

    ws.cell(row=row, column=3).value = "Report No:"
    ws.cell(row=row, column=3).font = bold
    ws.cell(row=row, column=4).value = report_number
    row += 1

    ws.cell(row=row, column=1).value = "Fund Cluster:"
    ws.cell(row=row, column=1).font = bold
    ws.cell(row=row, column=2).value = fund.fund_cluster.code

    ws.cell(row=row, column=3).value = "Sheet No:"
    ws.cell(row=row, column=3).font = bold
    ws.cell(row=row, column=4).value = sheet_number
    row += 2

    # =====================================================
    # TABLE HEADER
    # =====================================================
    headers = [
        "Date",
        "Petty Cash Voucher No.",
        "Particulars",
        "Amount"
    ]

    ws.append(headers)

    for col in range(1, 5):
        ws.cell(row=row, column=col).font = bold
        ws.cell(row=row, column=col).alignment = center
        ws.cell(row=row, column=col).border = border

    row += 1

    # =====================================================
    # TABLE DATA
    # =====================================================
    for v in vouchers:

        ws.cell(row=row, column=1).value = (
            v.purchase_date.strftime("%m-%d-%Y")
            if v.purchase_date else ""
        )

        ws.cell(row=row, column=2).value = v.pcv_no
        ws.cell(row=row, column=2).alignment = center

        ws.cell(row=row, column=3).value = (
            v.expense_category.name
            if v.expense_category else ""
        )
        ws.cell(row=row, column=3).alignment = wrap

        ws.cell(row=row, column=4).value = float(v.amount_requested)
        ws.cell(row=row, column=4).alignment = right

        for col in range(1, 5):
            ws.cell(row=row, column=col).border = border

        row += 1

    # =====================================================
    # TOTAL ROW
    # =====================================================
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    ws.cell(row=row, column=1).value = "TOTAL"
    ws.cell(row=row, column=1).alignment = right
    ws.cell(row=row, column=1).font = bold

    ws.cell(row=row, column=4).value = float(total)
    ws.cell(row=row, column=4).alignment = right
    ws.cell(row=row, column=4).font = bold

    for col in range(1, 5):
        ws.cell(row=row, column=col).border = border

    row += 3

    # =====================================================
    # CERTIFICATION
    # =====================================================
    ws.merge_cells(f"A{row}:D{row}")
    ws.cell(row=row, column=1).value = "C E R T I F I C A T I O N"
    ws.cell(row=row, column=1).font = bold
    ws.cell(row=row, column=1).alignment = center
    row += 2

    ws.merge_cells(f"A{row}:D{row}")
    ws.cell(row=row, column=1).value = \
        "I hereby certify to the correctness of the above information."
    ws.cell(row=row, column=1).alignment = center
    row += 4

    # =====================================================
    # SIGNATURE BLOCK (2 COLUMNS)
    # =====================================================
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
    ws.cell(row=row, column=1).value = fund.custodian.get_full_name().upper()
    ws.cell(row=row, column=1).font = bold
    ws.cell(row=row, column=1).alignment = center

    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)

    if date_to:
        date_value = date_to.strftime("%B %d, %Y")
    else:
        date_value = generated_date.strftime("%B %d, %Y")

    ws.cell(row=row, column=3).value = date_value
    ws.cell(row=row, column=3).font = bold
    ws.cell(row=row, column=3).alignment = center
    row += 1

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
    ws.cell(row=row, column=1).value = "Petty Cash Custodian"
    ws.cell(row=row, column=1).alignment = center

    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)
    ws.cell(row=row, column=3).value = f"Date: {generated_date.strftime('%B %d, %Y')}"
    ws.cell(row=row, column=3).alignment = center

    # =====================================================
    # COLUMN WIDTHS (MATCH PDF PROPORTION)
    # =====================================================
    ws.column_dimensions["A"].width = 18   # 15%
    ws.column_dimensions["B"].width = 30   # 25%
    ws.column_dimensions["C"].width = 50   # 40%
    ws.column_dimensions["D"].width = 20   # 20%

    # =====================================================
    # PAGE SETUP
    # =====================================================
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.fitToWidth = 1
    ws.print_area = f"A1:D{row}"