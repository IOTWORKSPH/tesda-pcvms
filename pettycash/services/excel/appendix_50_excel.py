# pettycash/services/excel/appendix_50_excel.py

from openpyxl.styles import Font, Alignment, Border, Side


def generate_appendix_50(wb, context, styles):

    fund = context["fund"]
    records = context["records"]
    generated_date = context["generated_date"]

    date_from = context.get("date_from")
    date_to = context.get("date_to")
    period_start = context.get("period_start")
    period_end = context.get("period_end")

    ws = wb.create_sheet("Appendix 50")

    bold = styles["bold"]
    bold_large = styles["bold_large"]
    center = styles["center"]
    right = styles["right"]
    border = styles["border"]
    wrap = styles["wrap"]

    row = 1

    # =====================================================
    # APPENDIX LABEL (Right)
    # =====================================================
    ws.merge_cells("A1:G1")
    ws["A1"] = "Appendix 50"
    ws["A1"].alignment = Alignment(horizontal="right")
    row += 1

    # =====================================================
    # TITLE
    # =====================================================
    ws.merge_cells(f"A{row}:G{row}")
    ws.cell(row=row, column=1).value = "PETTY CASH FUND RECORD"
    ws.cell(row=row, column=1).font = bold_large
    ws.cell(row=row, column=1).alignment = center
    row += 2

    # =====================================================
    # ENTITY + FUND
    # =====================================================
    ws.cell(row=row, column=1).value = "Entity Name :"
    ws.cell(row=row, column=1).font = bold
    ws.cell(row=row, column=2).value = fund.entity.name
    row += 1

    ws.cell(row=row, column=1).value = "Fund Cluster :"
    ws.cell(row=row, column=1).font = bold
    ws.cell(row=row, column=2).value = fund.fund_cluster.code
    row += 2

    # =====================================================
    # CUSTODIAN HEADER (3 columns)
    # =====================================================
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)
    ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=7)

    ws.cell(row=row, column=1).value = fund.custodian.get_full_name().upper()
    ws.cell(row=row, column=1).alignment = center
    ws.cell(row=row, column=1).font = bold

    ws.cell(row=row, column=3).value = fund.custodian.position or "-"
    ws.cell(row=row, column=3).alignment = center

    ws.cell(row=row, column=5).value = fund.custodian.office or fund.entity.name
    ws.cell(row=row, column=5).alignment = center
    row += 1

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
    ws.cell(row=row, column=1).value = "Petty Cash Fund Custodian"
    ws.cell(row=row, column=1).alignment = center

    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)
    ws.cell(row=row, column=3).value = "Official Designation"
    ws.cell(row=row, column=3).alignment = center

    ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=7)
    ws.cell(row=row, column=5).value = "Station"
    ws.cell(row=row, column=5).alignment = center
    row += 2

    # =====================================================
    # LEDGER TABLE HEADER
    # =====================================================
    headers = [
        "Date",
        "Reference",
        "Payee",
        "Particulars",
        "Receipts",
        "Disbursements",
        "Balance"
    ]

    ws.append(headers)

    for col in range(1, 8):
        ws.cell(row=row, column=col).font = bold
        ws.cell(row=row, column=col).alignment = center
        ws.cell(row=row, column=col).border = border

    row += 1

    # =====================================================
    # DATA ROWS
    # =====================================================
    for entry in records:

        ws.cell(row=row, column=1).value = (
            entry["date"].strftime("%B %d, %Y") if entry["date"] else ""
        )

        ws.cell(row=row, column=2).value = entry["reference"]
        ws.cell(row=row, column=3).value = entry["payee"]
        ws.cell(row=row, column=4).value = entry["particulars"]
        ws.cell(row=row, column=4).alignment = wrap

        ws.cell(row=row, column=5).value = float(entry["received"]) if entry["received"] else ""
        ws.cell(row=row, column=6).value = float(entry["disbursement"]) if entry["disbursement"] else ""
        ws.cell(row=row, column=7).value = float(entry["balance"]) if entry["balance"] else ""

        ws.cell(row=row, column=5).alignment = right
        ws.cell(row=row, column=6).alignment = right
        ws.cell(row=row, column=7).alignment = right

        for col in range(1, 8):
            ws.cell(row=row, column=col).border = border

        row += 1

    # =====================================================
    # PERIOD DISPLAY
    # =====================================================
    row += 1

    if date_from and date_to:
        period_text = f"{date_from.strftime('%B %d, %Y')} - {date_to.strftime('%B %d, %Y')}"
    elif period_start and period_end:
        period_text = f"{period_start.strftime('%B %d, %Y')} - {period_end.strftime('%B %d, %Y')}"
    else:
        period_text = "No Transactions Available"

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
    ws.cell(row=row, column=1).value = f"Period Covered: {period_text}"
    ws.cell(row=row, column=1).alignment = center
    row += 3

    # =====================================================
    # CERTIFICATION
    # =====================================================
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
    ws.cell(row=row, column=1).value = "C E R T I F I C A T I O N"
    ws.cell(row=row, column=1).font = bold
    ws.cell(row=row, column=1).alignment = center
    row += 2

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
    ws.cell(row=row, column=1).value = (
        f"I hereby certify that the foregoing is a correct and complete record of "
        f"all cash advances received and disbursements made by me in my capacity "
        f"as Petty Cash Fund Custodian of {fund.entity.name} during the period "
        f"{period_text}, inclusive, as indicated in the corresponding columns."
    )
    ws.cell(row=row, column=1).alignment = Alignment(horizontal="center", wrap_text=True)
    row += 4

    # =====================================================
    # SIGNATURE BLOCK
    # =====================================================
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    ws.cell(row=row, column=1).value = fund.custodian.get_full_name().upper()
    ws.cell(row=row, column=1).font = bold
    ws.cell(row=row, column=1).alignment = center

    ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=7)
    ws.cell(row=row, column=5).value = generated_date.strftime("%B %d, %Y")
    ws.cell(row=row, column=5).font = bold
    ws.cell(row=row, column=5).alignment = center
    row += 1

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    ws.cell(row=row, column=1).value = "Name and Signature of Petty Cash Fund Custodian"
    ws.cell(row=row, column=1).alignment = center

    ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=7)
    ws.cell(row=row, column=5).value = "Date"
    ws.cell(row=row, column=5).alignment = center

    # =====================================================
    # COLUMN WIDTHS
    # =====================================================
    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 30
    ws.column_dimensions["E"].width = 15
    ws.column_dimensions["F"].width = 15
    ws.column_dimensions["G"].width = 15

    # =====================================================
    # PAGE SETUP
    # =====================================================
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.fitToWidth = 1
    ws.print_area = f"A1:G{row}"