# pettycash/services/replenishment_pdf.py

from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML


def generate_replenishment_pdf(request, context):

    html_string = render_to_string(
        "pettycash/reports/replenishment_package_pdf.html",
        context
    )

    pdf = HTML(
        string=html_string,
        base_url=request.build_absolute_uri()
    ).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=replenishment_package.pdf"

    return response