import subprocess
import shutil
import uuid
from pathlib import Path

from django.conf import settings
from openpyxl.worksheet.properties import PageSetupProperties


class ExcelPdfExportError(RuntimeError):
    pass


def configure_print_layout(workbook, orientation="portrait", print_area=None):
    worksheet = workbook.active

    if print_area:
        worksheet.print_area = print_area

    worksheet.page_setup.orientation = orientation
    worksheet.page_setup.paperSize = 9
    worksheet.page_setup.fitToWidth = 1
    worksheet.page_setup.fitToHeight = 1
    worksheet.page_setup.scale = None

    if worksheet.sheet_properties.pageSetUpPr is None:
        worksheet.sheet_properties.pageSetUpPr = PageSetupProperties()

    worksheet.sheet_properties.pageSetUpPr.fitToPage = True

    return workbook


def export_workbooks_to_pdf(workbooks):
    scratch_root = Path(settings.BASE_DIR) / ".tmp" / "excel_pdf"
    scratch_root.mkdir(parents=True, exist_ok=True)

    temp_path = scratch_root / f"tesda_pcvms_pdf_{uuid.uuid4().hex}"
    temp_path.mkdir(parents=True, exist_ok=True)

    try:
        input_paths = []

        for index, workbook in enumerate(workbooks, start=1):
            workbook_path = temp_path / f"document_{index}.xlsx"
            workbook.save(workbook_path)
            input_paths.append(workbook_path)

        pdf_path = temp_path / "documents.pdf"
        script_path = temp_path / "export_excel_pdf.ps1"
        script_path.write_text(
            _build_export_script(input_paths, pdf_path),
            encoding="utf-8",
        )

        try:
            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script_path),
                ],
                capture_output=True,
                text=True,
                timeout=90,
            )
        except subprocess.TimeoutExpired as exc:
            raise ExcelPdfExportError("Excel PDF export timed out.") from exc

        if result.returncode != 0:
            error = (result.stderr or result.stdout or "Excel PDF export failed").strip()
            raise ExcelPdfExportError(error)

        if not pdf_path.exists():
            raise ExcelPdfExportError("Excel PDF export did not create a PDF file.")

        return pdf_path.read_bytes()
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


def _build_export_script(input_paths, pdf_path):
    path_list = ", ".join(_ps_quote(path) for path in input_paths)
    return f"""
$ErrorActionPreference = 'Stop'
$inputPaths = @({path_list})
$pdfPath = {_ps_quote(pdf_path)}
$excel = $null
$combined = $null
$blank = $null

try {{
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.ScreenUpdating = $false
    $excel.SheetsInNewWorkbook = 1

    if ($inputPaths.Count -eq 1) {{
        $combined = $excel.Workbooks.Open($inputPaths[0])
    }} else {{
        $combined = $excel.Workbooks.Add()
        $blank = $combined.Worksheets.Item(1)

        foreach ($path in $inputPaths) {{
            $source = $null
            try {{
                $source = $excel.Workbooks.Open($path)
                $source.Worksheets.Item(1).Copy($null, $combined.Worksheets.Item($combined.Worksheets.Count))
            }} finally {{
                if ($source -ne $null) {{
                    $source.Close($false) | Out-Null
                    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($source) | Out-Null
                }}
            }}
        }}

        $blank.Delete()
    }}

    $combined.ExportAsFixedFormat(0, $pdfPath)
}} finally {{
    if ($combined -ne $null) {{
        $combined.Close($false) | Out-Null
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($combined) | Out-Null
    }}

    if ($excel -ne $null) {{
        $excel.Quit() | Out-Null
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    }}

    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}}
"""


def _ps_quote(path):
    return "'" + str(path).replace("'", "''") + "'"
