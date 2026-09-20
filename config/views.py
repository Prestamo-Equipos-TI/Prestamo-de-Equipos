from django.shortcuts import render


def error_500(request):
    return render(
        request,
        "pages/errors/500.html",
        status=500
    )