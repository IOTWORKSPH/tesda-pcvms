# pettycash/services/excel/excel_styles.py

from openpyxl.styles import Font, Alignment, Border, Side

def get_styles():

    bold = Font(bold=True)
    bold_large = Font(bold=True, size=14)

    center = Alignment(horizontal="center", vertical="center")
    right = Alignment(horizontal="right", vertical="center")
    left = Alignment(horizontal="left", vertical="center")

    wrap = Alignment(wrap_text=True, vertical="top")
    wrap_center = Alignment(wrap_text=True, horizontal="center", vertical="center")
    wrap_right = Alignment(wrap_text=True, horizontal="right", vertical="center")

    thin = Side(style="thin")
    border = Border(
        left=thin,
        right=thin,
        top=thin,
        bottom=thin
    )

    return {
        "bold": bold,
        "bold_large": bold_large,
        "center": center,
        "right": right,
        "left": left,
        "wrap": wrap,
        "wrap_center": wrap_center,
        "wrap_right": wrap_right,
        "border": border,
    }