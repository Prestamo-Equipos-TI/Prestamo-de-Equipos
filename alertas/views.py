from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Alerta


@login_required
def alertas_lista(request):
    alertas = Alerta.objects.filter(
        usuario=request.user
    ).order_by('-fecha_creacion')

    Alerta.objects.filter(
        usuario=request.user,
        leida=False
    ).update(leida=True)

    context = {
        'active_page': 'alertas',
        'content_template': 'pages/alertas/lista_content.html',
        'alertas': alertas,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/alertas/lista_content.html', context)

    return render(request, 'pages/app_layout.html', context)