from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from inventario.models import Equipo
from .models import SolicitudPrestamo
from .forms import SolicitudPrestamoForm


@login_required
def solicitar_prestamo_lista(request):
    equipos = Equipo.objects.filter(
        activo=True,
        estado='disponible'
    ).order_by('nombre')

    context = {
        'active_page': 'solicitar_prestamo',
        'content_template': 'pages/prestamos/solicitar_content.html',
        'equipos': equipos,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/prestamos/solicitar_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
def crear_solicitud_prestamo(request, equipo_id):
    equipo = get_object_or_404(
        Equipo,
        id=equipo_id,
        activo=True,
        estado='disponible'
    )

    es_htmx = request.headers.get('HX-Request')

    if request.method == 'POST':
        form = SolicitudPrestamoForm(request.POST)

        if form.is_valid():
            solicitud_pendiente = SolicitudPrestamo.objects.filter(
                usuario=request.user,
                equipo=equipo,
                estado=SolicitudPrestamo.ESTADO_PENDIENTE
            ).exists()

            if solicitud_pendiente:
                form.add_error(
                    None,
                    'Ya tienes una solicitud pendiente para este equipo.'
                )

                if es_htmx:
                    return render(request, 'pages/prestamos/formulario_solicitud.html', {
                        'form': form,
                        'equipo': equipo,
                        'es_modal': True,
                    }, status=422)

                return render(request, 'pages/prestamos/formulario_solicitud.html', {
                    'form': form,
                    'equipo': equipo,
                    'es_modal': False,
                })

            solicitud = form.save(commit=False)
            solicitud.usuario = request.user
            solicitud.equipo = equipo
            solicitud.estado = SolicitudPrestamo.ESTADO_PENDIENTE
            solicitud.save()

            if es_htmx:
                return HttpResponse(status=204)

            return redirect('prestamos:mis_solicitudes')

        if es_htmx:
            return render(request, 'pages/prestamos/formulario_solicitud.html', {
                'form': form,
                'equipo': equipo,
                'es_modal': True,
            }, status=422)

    else:
        form = SolicitudPrestamoForm()

    return render(request, 'pages/prestamos/formulario_solicitud.html', {
        'form': form,
        'equipo': equipo,
        'es_modal': bool(es_htmx),
    })


@login_required
def mis_solicitudes(request):
    solicitudes = SolicitudPrestamo.objects.filter(
        usuario=request.user
    ).select_related('equipo').order_by('-fecha_solicitud')

    context = {
        'active_page': 'mis_solicitudes',
        'content_template': 'pages/prestamos/mis_solicitudes_content.html',
        'solicitudes': solicitudes,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/prestamos/mis_solicitudes_content.html', context)

    return render(request, 'pages/app_layout.html', context)