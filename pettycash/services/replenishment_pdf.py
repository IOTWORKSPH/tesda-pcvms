# pettycash/services/replenishment_pdf.py

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string


def generate_replenishment_pdf(request, context):
    """
    Generate replenishment PDF using WeasyPrint.

    Local development:
    - If WEASYPRINT_ENABLED=False, this raises RuntimeError instead of
      breaking Django startup.

    Production:
    - If WEASYPRINT_ENABLED=True and WeasyPrint native dependencies are
      installed, PDF generation works normally.
    """

    if not getattr(settings, "WEASYPRINT_ENABLED", False):
        raise RuntimeError("PDF generation is disabled in this environment.")

    try:
        from weasyprint import HTML
    except Exception as exc:
        raise RuntimeError(
            "WeasyPrint is not available in this environment. "
            "Install the required dependencies on production, or keep "
            "WEASYPRINT_ENABLED=False for local development."
        ) from exc

    html_string = render_to_string(
        "pettycash/reports/replenishment_package_pdf.html",
        context,
        request=request,
    )

    pdf = HTML(
        string=html_string,
        base_url=request.build_absolute_uri("/"),
    ).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=replenishment_package.pdf"
    return response