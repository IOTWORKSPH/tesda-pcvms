#Core Views.py codes
from django.http import HttpResponse
from django.shortcuts import render


def custom_403(request, exception):
    return render(request, "403.html", status=403)


def robots_txt(request):
    return HttpResponse(
        "User-agent: *\nDisallow: /\n",
        content_type="text/plain",
    )
