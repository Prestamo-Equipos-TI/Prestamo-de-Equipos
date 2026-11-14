from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse

from config.reportes import exportar_reporte, filtrar_periodo, periodo_reporte
from usuarios.models import PerfilUsuario
from usuarios.permisos import rol_funcional

from .models import Alerta


@login_required
def alertas_lista(request):
    puede_exportar = rol_funcional(request.user) in (
        PerfilUsuario.ROL_ADMIN_TI, PerfilUsuario.ROL_SUPERADMIN)
    desde, hasta, error_periodo = periodo_reporte(request)
    tipo = request.GET.get('tipo', '').strip()
    tipos = dict(Alerta.TIPOS)
    error_tipo = 'Selecciona un tipo de alerta válido.' if tipo and tipo not in tipos else None
    alertas = Alerta.objects.filter(
        usuario=request.user
    ).order_by('-fecha_creacion')
    if not error_periodo and not error_tipo:
        alertas = filtrar_periodo(alertas, 'fecha_creacion', desde, hasta)
        if tipo:
            alertas = alertas.filter(tipo=tipo)

    if request.GET.get('export') == 'pdf':
        if not puede_exportar:
            return HttpResponseForbidden('Acceso reservado a gestión TI')
        if error_periodo or error_tipo:
            return HttpResponse(error_periodo or error_tipo, status=400)
        filas = [(a.titulo, a.mensaje, a.get_tipo_display(),
                  'Leída' if a.leida else 'Nueva', a.fecha_creacion) for a in alertas]
        return exportar_reporte('pdf', 'alertas', 'Mis alertas', [
            ('Alertas', ['Título', 'Mensaje', 'Tipo', 'Estado', 'Fecha'], filas),
        ], usuario=request.user, desde=desde, hasta=hasta,
            filtros={'Tipo de alerta': tipos[tipo]} if tipo else None)

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
        'fecha_inicio': request.GET.get('fecha_inicio', ''),
        'fecha_fin': request.GET.get('fecha_fin', ''),
        'tipo': tipo,
        'tipos': Alerta.TIPOS,
        'error_filtros': error_periodo or error_tipo,
        'puede_exportar_alertas': puede_exportar,
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
