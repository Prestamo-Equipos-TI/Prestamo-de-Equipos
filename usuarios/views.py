from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    context = {
        'active_page': 'dashboard',
        'content_template': 'pages/dashboard_content.html',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/dashboard_content.html', context)

    return render(request, 'pages/app_layout.html', context)