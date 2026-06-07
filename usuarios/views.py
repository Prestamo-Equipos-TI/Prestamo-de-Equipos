from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from alertas.models import Alerta


@login_required
def dashboard(request):
    # Verifica si el usuario tiene alertas no leídas para mostrar badge
    context = {
        'active_page': 'dashboard',
        'content_template': 'pages/dashboard_content.html',
        'tiene_alertas_nuevas': Alerta.objects.filter(
            usuario=request.user,
            leida=False
        ).exists(),
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/dashboard_content.html', context)

    return render(request, 'pages/app_layout.html', context)
