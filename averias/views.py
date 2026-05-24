from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from alertas.models import Alerta
from inventario.models import Equipo
from prestamos.models import SolicitudPrestamo
from usuarios.models import PerfilUsuario

from .forms import GestionarAveriaForm, ReporteAveriaForm, ResolverAveriaForm
from .models import ReporteAveria


def existe_reporte_activo(equipo):
    return ReporteAveria.objects.filter(
        equipo=equipo,
        estado__in=[
            ReporteAveria.ESTADO_PENDIENTE,
            ReporteAveria.ESTADO_EN_REVISION
        ]
    ).exists()


@login_required
def reportar_averia_lista(request):
    prestamos_activos = SolicitudPrestamo.objects.select_related(
        'equipo'
    ).filter(
        usuario=request.user,
        estado=SolicitudPrestamo.ESTADO_ENTREGADO,
        equipo__estado='prestado'
    ).order_by('equipo__nombre')

    context = {
        'active_page': 'reportar_averia',
        'content_template': 'pages/averias/reportar_content.html',
        'prestamos_activos': prestamos_activos,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/averias/reportar_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
def reportar_averia_modal(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_related('equipo'),
        id=solicitud_id,
        usuario=request.user,
        estado=SolicitudPrestamo.ESTADO_ENTREGADO,
        equipo__estado='prestado'
    )

    form = ReporteAveriaForm()

    return render(request, 'pages/averias/reportar_modal.html', {
        'form': form,
        'solicitud': solicitud,
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
def confirmar_reporte_averia(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_related('equipo'),
        id=solicitud_id,
        usuario=request.user,
        estado=SolicitudPrestamo.ESTADO_ENTREGADO,
        equipo__estado='prestado'
    )

    es_htmx = request.headers.get('HX-Request')

    if request.method == 'POST':
        form = ReporteAveriaForm(request.POST)

        if form.is_valid():
            if existe_reporte_activo(solicitud.equipo):
                form.add_error(
                    None,
                    'Ya existe un reporte de avería activo para este equipo.'
                )

                if es_htmx:
                    return render(request, 'pages/averias/reportar_modal.html', {
                        'form': form,
                        'solicitud': solicitud,
                        'es_modal': True,
                    }, status=422)

                return redirect('averias:reportar')

            ReporteAveria.objects.create(
                equipo=solicitud.equipo,
                solicitud_prestamo=solicitud,
                reportado_por=request.user,
                descripcion_falla=form.cleaned_data['descripcion_falla'],
                estado=ReporteAveria.ESTADO_PENDIENTE
            )

            Alerta.objects.create(
                usuario=request.user,
                titulo='Reporte de avería enviado',
                mensaje=(
                    f'Tu reporte de avería para el equipo '
                    f'{solicitud.equipo.nombre} fue enviado correctamente. '
                    f'El área de TI revisará el caso.'
                ),
                tipo=Alerta.TIPO_SISTEMA
            )

            administradores_ti = PerfilUsuario.objects.filter(
                rol=PerfilUsuario.ROL_ADMIN_TI
            ).select_related('user')

            for perfil_admin in administradores_ti:
                Alerta.objects.create(
                    usuario=perfil_admin.user,
                    titulo='Nueva avería reportada',
                    mensaje=(
                        f'Se reportó una avería para el equipo '
                        f'{solicitud.equipo.nombre}.'
                    ),
                    tipo=Alerta.TIPO_SISTEMA
                )

            if es_htmx:
                return HttpResponse(status=204)

            return redirect('averias:reportar')

        if es_htmx:
            return render(request, 'pages/averias/reportar_modal.html', {
                'form': form,
                'solicitud': solicitud,
                'es_modal': True,
            }, status=422)

    return redirect('averias:reportar')


@login_required
def averias_admin_inicio(request):
    context = {
        'active_page': 'averias_admin',
        'content_template': 'pages/averias/averias_admin_content.html',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/averias/averias_admin_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
def averias_admin_lista(request):
    reportes = ReporteAveria.objects.select_related(
        'equipo',
        'reportado_por',
        'reportado_por__perfil',
        'solicitud_prestamo'
    ).order_by('-fecha_reporte')

    context = {
        'active_page': 'averias_admin',
        'content_template': 'pages/averias/admin_content.html',
        'reportes': reportes,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/averias/admin_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
def reporte_administrativo_lista(request):
    equipos = Equipo.objects.filter(
        activo=True,
        estado__in=['averiado', 'mantenimiento']
    ).order_by('nombre')

    context = {
        'active_page': 'averias_admin',
        'content_template': 'pages/averias/reporte_administrativo_content.html',
        'equipos': equipos,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/averias/reporte_administrativo_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
def reporte_administrativo_modal(request, equipo_id):
    equipo = get_object_or_404(
        Equipo,
        id=equipo_id,
        activo=True,
        estado__in=['averiado', 'mantenimiento']
    )

    form = ReporteAveriaForm()

    return render(request, 'pages/averias/reporte_admin_modal.html', {
        'form': form,
        'equipo': equipo,
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
def confirmar_reporte_administrativo(request, equipo_id):
    equipo = get_object_or_404(
        Equipo,
        id=equipo_id,
        activo=True,
        estado__in=['averiado', 'mantenimiento']
    )

    es_htmx = request.headers.get('HX-Request')

    if request.method == 'POST':
        form = ReporteAveriaForm(request.POST)

        if form.is_valid():
            if existe_reporte_activo(equipo):
                form.add_error(
                    None,
                    'Este equipo ya tiene un reporte de avería activo.'
                )

                if es_htmx:
                    return render(request, 'pages/averias/reporte_admin_modal.html', {
                        'form': form,
                        'equipo': equipo,
                        'es_modal': True,
                    }, status=422)

                return redirect('averias:reporte_administrativo')

            ReporteAveria.objects.create(
                equipo=equipo,
                solicitud_prestamo=None,
                reportado_por=request.user,
                descripcion_falla=form.cleaned_data['descripcion_falla'],
                estado=ReporteAveria.ESTADO_PENDIENTE
            )

            Alerta.objects.create(
                usuario=request.user,
                titulo='Reporte administrativo registrado',
                mensaje=(
                    f'Se registró correctamente un reporte administrativo '
                    f'para el equipo {equipo.nombre}.'
                ),
                tipo=Alerta.TIPO_SISTEMA
            )

            if es_htmx:
                return HttpResponse(status=204)

            return redirect('averias:reporte_administrativo')

        if es_htmx:
            return render(request, 'pages/averias/reporte_admin_modal.html', {
                'form': form,
                'equipo': equipo,
                'es_modal': True,
            }, status=422)

    return redirect('averias:reporte_administrativo')


@login_required
def gestionar_averia_modal(request, reporte_id):
    reporte = get_object_or_404(
        ReporteAveria.objects.select_related(
            'equipo',
            'reportado_por',
            'reportado_por__perfil',
            'solicitud_prestamo'
        ),
        id=reporte_id,
        estado__in=[
            ReporteAveria.ESTADO_PENDIENTE,
            ReporteAveria.ESTADO_EN_REVISION
        ]
    )

    form = GestionarAveriaForm()

    return render(request, 'pages/averias/gestionar_modal.html', {
        'form': form,
        'reporte': reporte,
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
def confirmar_gestion_averia(request, reporte_id):
    reporte = get_object_or_404(
        ReporteAveria.objects.select_related(
            'equipo',
            'reportado_por',
            'reportado_por__perfil',
            'solicitud_prestamo'
        ),
        id=reporte_id,
        estado__in=[
            ReporteAveria.ESTADO_PENDIENTE,
            ReporteAveria.ESTADO_EN_REVISION
        ]
    )

    es_htmx = request.headers.get('HX-Request')

    if request.method == 'POST':
        form = GestionarAveriaForm(request.POST)

        if form.is_valid():
            accion_tomada = form.cleaned_data['accion_tomada']

            reporte.estado = ReporteAveria.ESTADO_EN_REVISION
            reporte.revisado_por = request.user
            reporte.fecha_revision = timezone.now()
            reporte.accion_tomada = accion_tomada
            reporte.observaciones_revision = form.cleaned_data['observaciones_revision']
            reporte.save()

            equipo = reporte.equipo

            if accion_tomada == GestionarAveriaForm.ACCION_MANTENIMIENTO:
                equipo.estado = 'mantenimiento'
                equipo.save()

            elif accion_tomada == GestionarAveriaForm.ACCION_AVERIADO:
                equipo.estado = 'averiado'
                equipo.save()

            elif accion_tomada == GestionarAveriaForm.ACCION_VISITA_EXTERNA:
                equipo.estado = 'mantenimiento'
                equipo.save()

            if reporte.reportado_por:
                Alerta.objects.create(
                    usuario=reporte.reportado_por,
                    titulo='Avería en revisión',
                    mensaje=(
                        f'El reporte de avería del equipo {reporte.equipo.nombre} '
                        f'ha sido tomado en revisión por el área de TI.'
                    ),
                    tipo=Alerta.TIPO_SISTEMA
                )

            if es_htmx:
                return HttpResponse(status=204)

            return redirect('averias:admin_lista')

        if es_htmx:
            return render(request, 'pages/averias/gestionar_modal.html', {
                'form': form,
                'reporte': reporte,
                'es_modal': True,
            }, status=422)

    return redirect('averias:admin_lista')

@login_required
def resolver_averia_modal(request, reporte_id):
    reporte = get_object_or_404(
        ReporteAveria.objects.select_related(
            'equipo',
            'reportado_por',
            'reportado_por__perfil',
            'solicitud_prestamo'
        ),
        id=reporte_id,
        estado=ReporteAveria.ESTADO_EN_REVISION
    )

    form = ResolverAveriaForm()

    return render(request, 'pages/averias/resolver_modal.html', {
        'form': form,
        'reporte': reporte,
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
def confirmar_resolucion_averia(request, reporte_id):
    reporte = get_object_or_404(
        ReporteAveria.objects.select_related(
            'equipo',
            'reportado_por',
            'reportado_por__perfil',
            'solicitud_prestamo'
        ),
        id=reporte_id,
        estado=ReporteAveria.ESTADO_EN_REVISION
    )

    es_htmx = request.headers.get('HX-Request')

    if request.method == 'POST':
        form = ResolverAveriaForm(request.POST)

        if form.is_valid():
            reporte.estado = ReporteAveria.ESTADO_RESUELTA
            reporte.resuelto_por = request.user
            reporte.fecha_resolucion = timezone.now()
            reporte.observaciones_resolucion = form.cleaned_data['observaciones_resolucion']
            reporte.save()

            if reporte.solicitud_prestamo is None:
                estado_final_equipo = form.cleaned_data['estado_final_equipo']

                if estado_final_equipo != ResolverAveriaForm.ESTADO_SIN_CAMBIO:
                    equipo = reporte.equipo
                    equipo.estado = estado_final_equipo
                    equipo.save()

            if reporte.reportado_por:
                Alerta.objects.create(
                    usuario=reporte.reportado_por,
                    titulo='Avería resuelta',
                    mensaje=(
                        f'El reporte de avería del equipo {reporte.equipo.nombre} '
                        f'ha sido marcado como resuelto por el área de TI.'
                    ),
                    tipo=Alerta.TIPO_SISTEMA
                )

            if es_htmx:
                return HttpResponse(status=204)

            return redirect('averias:admin_lista')

        if es_htmx:
            return render(request, 'pages/averias/resolver_modal.html', {
                'form': form,
                'reporte': reporte,
                'es_modal': True,
            }, status=422)

    return redirect('averias:admin_lista')