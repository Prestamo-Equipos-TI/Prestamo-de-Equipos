from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Alerta


@login_required
def alertas_lista(request):
    alertas = Alerta.objects.filter(
        usuario=request.user
    ).order_by('-fecha_creacion')

    # Marca todas las alertas del usuario como leídas
    # cuando entra al módulo de alertas.
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
        return render(
            request,
            'pages/alertas/lista_content.html',
            context
        )

    return render(
        request,
        'pages/app_layout.html',
        context
    )


@login_required
def alerta_nueva(request):

    alerta = Alerta.objects.filter(
        usuario=request.user,
        leida=False
    ).order_by('-fecha_creacion').first()

    if not alerta:
        return JsonResponse({
            'hay_nueva': False
        })

    return JsonResponse({
        'hay_nueva': True,
        'id': alerta.id,
        'titulo': alerta.titulo,
        'mensaje': alerta.mensaje,
        'tipo': alerta.tipo,
    })