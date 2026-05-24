from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from alertas.models import Alerta
from inventario.models import Equipo
from usuarios.models import PerfilUsuario
from .services import detectar_prestamos_vencidos
from .forms import SolicitudPrestamoForm
from .forms_aprobacion import AprobarSolicitudForm
from .forms_devolucion import RegistrarDevolucionForm
from .forms_entrega import RegistrarEntregaForm
from .models import SolicitudPrestamo


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

                return render(request, 'pages/prestamos/formulario_solicitud.html', {
                    'form': form,
                    'equipo': equipo,
                    'es_modal': bool(es_htmx),
                }, status=422 if es_htmx else 200)

            solicitud = form.save(commit=False)
            solicitud.usuario = request.user
            solicitud.equipo = equipo
            solicitud.estado = SolicitudPrestamo.ESTADO_PENDIENTE
            solicitud.save()

            administradores_ti = PerfilUsuario.objects.filter(
                rol=PerfilUsuario.ROL_ADMIN_TI
            ).select_related('user')

            for perfil_admin in administradores_ti:
                Alerta.objects.create(
                    usuario=perfil_admin.user,
                    titulo='Nueva solicitud de préstamo',
                    mensaje=(
                        f'Hay una nueva solicitud pendiente para el equipo '
                        f'{equipo.nombre}.'
                    ),
                    tipo=Alerta.TIPO_SISTEMA
                )

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


@login_required
def solicitudes_admin(request):
    solicitudes = SolicitudPrestamo.objects.select_related(
        'usuario',
        'usuario__perfil',
        'equipo'
    ).order_by('-fecha_solicitud')

    context = {
        'active_page': 'solicitudes_admin',
        'content_template': 'pages/prestamos/solicitudes_admin_content.html',
        'solicitudes': solicitudes,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/prestamos/solicitudes_admin_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
def prestamos_admin_inicio(request):
    detectar_prestamos_vencidos()

    context = {
        'active_page': 'prestamos_admin',
        'content_template': 'pages/prestamos/prestamos_admin_content.html',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/prestamos/prestamos_admin_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
def aprobar_solicitud_modal(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_related(
            'usuario',
            'usuario__perfil',
            'equipo'
        ),
        id=solicitud_id,
        estado=SolicitudPrestamo.ESTADO_PENDIENTE
    )

    form = AprobarSolicitudForm()

    return render(request, 'pages/prestamos/aprobar_solicitud_modal.html', {
        'form': form,
        'solicitud': solicitud,
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
@transaction.atomic
def confirmar_aprobacion_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_related(
            'usuario',
            'usuario__perfil',
            'equipo'
        ),
        id=solicitud_id,
        estado=SolicitudPrestamo.ESTADO_PENDIENTE
    )

    es_htmx = request.headers.get('HX-Request')

    if request.method == 'POST':
        form = AprobarSolicitudForm(request.POST)

        if form.is_valid():
            solicitud.fecha_entrega_programada = form.cleaned_data['fecha_entrega_programada']
            solicitud.dias_prestamo = form.cleaned_data['dias_prestamo']
            solicitud.estado = SolicitudPrestamo.ESTADO_APROBADO
            solicitud.aprobado_por = request.user
            solicitud.save()

            equipo = solicitud.equipo
            equipo.estado = 'reservado'
            equipo.save()

            solicitudes_rechazadas = SolicitudPrestamo.objects.filter(
                equipo=equipo,
                estado=SolicitudPrestamo.ESTADO_PENDIENTE
            ).exclude(
                id=solicitud.id
            )

            usuarios_rechazados = list(
                solicitudes_rechazadas.select_related('usuario')
            )

            solicitudes_rechazadas.update(
                estado=SolicitudPrestamo.ESTADO_RECHAZADO,
                rechazado_por=request.user
            )

            Alerta.objects.create(
                usuario=solicitud.usuario,
                titulo='Solicitud de préstamo aprobada',
                mensaje=(
                    f'Tu solicitud del equipo {equipo.nombre} ha sido aprobada. '
                    f'Entrega programada: {solicitud.fecha_entrega_programada}. '
                    f'Duración: {solicitud.dias_prestamo} día(s).'
                ),
                tipo=Alerta.TIPO_PRESTAMO_APROBADO
            )

            for solicitud_rechazada in usuarios_rechazados:
                Alerta.objects.create(
                    usuario=solicitud_rechazada.usuario,
                    titulo='Solicitud de préstamo rechazada',
                    mensaje=(
                        f'Tu solicitud del equipo {equipo.nombre} fue rechazada '
                        f'porque el equipo ya fue reservado.'
                    ),
                    tipo=Alerta.TIPO_PRESTAMO_RECHAZADO
                )

            if es_htmx:
                return HttpResponse(status=204)

            return redirect('prestamos:solicitudes_admin')

        if es_htmx:
            return render(request, 'pages/prestamos/aprobar_solicitud_modal.html', {
                'form': form,
                'solicitud': solicitud,
                'es_modal': True,
            }, status=422)

    return redirect('prestamos:solicitudes_admin')


@login_required
@transaction.atomic
def rechazar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_related(
            'usuario',
            'equipo'
        ),
        id=solicitud_id,
        estado=SolicitudPrestamo.ESTADO_PENDIENTE
    )

    if request.method == 'POST':
        solicitud.estado = SolicitudPrestamo.ESTADO_RECHAZADO
        solicitud.rechazado_por = request.user
        solicitud.save()

        Alerta.objects.create(
            usuario=solicitud.usuario,
            titulo='Solicitud de préstamo rechazada',
            mensaje=(
                f'Tu solicitud del equipo {solicitud.equipo.nombre} '
                f'ha sido rechazada por el área de TI.'
            ),
            tipo=Alerta.TIPO_PRESTAMO_RECHAZADO
        )

        if request.headers.get('HX-Request'):
            return HttpResponse(status=204)

        return redirect('prestamos:solicitudes_admin')

    return redirect('prestamos:solicitudes_admin')


@login_required
def entregas_lista(request):
    solicitudes = SolicitudPrestamo.objects.select_related(
        'usuario',
        'usuario__perfil',
        'equipo'
    ).filter(
        estado=SolicitudPrestamo.ESTADO_APROBADO,
        equipo__estado='reservado'
    ).order_by('fecha_entrega_programada')

    context = {
        'active_page': 'prestamos_admin',
        'content_template': 'pages/prestamos/entregas_content.html',
        'solicitudes': solicitudes,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/prestamos/entregas_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
def registrar_entrega_modal(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_related(
            'usuario',
            'usuario__perfil',
            'equipo'
        ),
        id=solicitud_id,
        estado=SolicitudPrestamo.ESTADO_APROBADO,
        equipo__estado='reservado'
    )

    form = RegistrarEntregaForm()

    return render(request, 'pages/prestamos/registrar_entrega_modal.html', {
        'form': form,
        'solicitud': solicitud,
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
@transaction.atomic
def confirmar_entrega(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_related(
            'usuario',
            'usuario__perfil',
            'equipo'
        ),
        id=solicitud_id,
        estado=SolicitudPrestamo.ESTADO_APROBADO,
        equipo__estado='reservado'
    )

    es_htmx = request.headers.get('HX-Request')

    if request.method == 'POST':
        form = RegistrarEntregaForm(request.POST)

        if form.is_valid():
            fecha_real = form.cleaned_data['fecha_entrega_real']
            observaciones = form.cleaned_data['observaciones_entrega']

            solicitud.fecha_entrega_real = fecha_real
            solicitud.fecha_devolucion_estimada = fecha_real + timedelta(
                days=solicitud.dias_prestamo
            )
            solicitud.observaciones_entrega = observaciones
            solicitud.estado = SolicitudPrestamo.ESTADO_ENTREGADO
            solicitud.entregado_por = request.user
            solicitud.save()

            equipo = solicitud.equipo
            equipo.estado = 'prestado'
            equipo.save()

            Alerta.objects.create(
                usuario=solicitud.usuario,
                titulo='Equipo entregado',
                mensaje=(
                    f'Se registró la entrega del equipo {equipo.nombre}. '
                    f'Fecha estimada de devolución: '
                    f'{solicitud.fecha_devolucion_estimada}.'
                ),
                tipo=Alerta.TIPO_PRESTAMO_ENTREGADO
            )

            if es_htmx:
                return HttpResponse(status=204)

            return redirect('prestamos:entregas')

        if es_htmx:
            return render(request, 'pages/prestamos/registrar_entrega_modal.html', {
                'form': form,
                'solicitud': solicitud,
                'es_modal': True,
            }, status=422)

    return redirect('prestamos:entregas')


@login_required
def equipos_prestados(request):
    solicitudes = SolicitudPrestamo.objects.select_related(
        'usuario',
        'usuario__perfil',
        'equipo'
    ).filter(
        estado=SolicitudPrestamo.ESTADO_ENTREGADO,
        equipo__estado='prestado'
    ).order_by('-fecha_entrega_real')

    context = {
        'active_page': 'prestamos_admin',
        'content_template': 'pages/prestamos/equipos_prestados_content.html',
        'solicitudes': solicitudes,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/prestamos/equipos_prestados_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
def detalle_prestamo(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_related(
            'usuario',
            'usuario__perfil',
            'equipo'
        ),
        id=solicitud_id,
        estado=SolicitudPrestamo.ESTADO_ENTREGADO,
        equipo__estado='prestado'
    )

    return render(request, 'pages/prestamos/detalle_prestamo_modal.html', {
        'solicitud': solicitud,
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
def devoluciones_lista(request):
    solicitudes = SolicitudPrestamo.objects.select_related(
        'usuario',
        'usuario__perfil',
        'equipo'
    ).filter(
        estado=SolicitudPrestamo.ESTADO_ENTREGADO,
        equipo__estado='prestado'
    ).order_by('fecha_devolucion_estimada')

    context = {
        'active_page': 'prestamos_admin',
        'content_template': 'pages/prestamos/devoluciones_content.html',
        'solicitudes': solicitudes,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/prestamos/devoluciones_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
def registrar_devolucion_modal(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_related(
            'usuario',
            'usuario__perfil',
            'equipo'
        ),
        id=solicitud_id,
        estado=SolicitudPrestamo.ESTADO_ENTREGADO,
        equipo__estado='prestado'
    )

    form = RegistrarDevolucionForm()

    return render(request, 'pages/prestamos/registrar_devolucion_modal.html', {
        'form': form,
        'solicitud': solicitud,
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
@transaction.atomic
def confirmar_devolucion(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_related(
            'usuario',
            'usuario__perfil',
            'equipo'
        ),
        id=solicitud_id,
        estado=SolicitudPrestamo.ESTADO_ENTREGADO,
        equipo__estado='prestado'
    )

    es_htmx = request.headers.get('HX-Request')

    if request.method == 'POST':
        form = RegistrarDevolucionForm(request.POST)

        if form.is_valid():
            solicitud.fecha_devolucion_real = form.cleaned_data['fecha_devolucion_real']
            solicitud.observaciones_devolucion = form.cleaned_data['observaciones_devolucion']
            solicitud.estado = SolicitudPrestamo.ESTADO_DEVUELTO
            solicitud.devuelto_por = request.user
            solicitud.save()

            equipo = solicitud.equipo
            equipo.estado = 'disponible'
            equipo.save()

            Alerta.objects.create(
                usuario=solicitud.usuario,
                titulo='Equipo devuelto',
                mensaje=(
                    f'Se registró correctamente la devolución del equipo '
                    f'{equipo.nombre}. Gracias por completar el préstamo.'
                ),
                tipo=Alerta.TIPO_PRESTAMO_DEVUELTO
            )

            if es_htmx:
                return HttpResponse(status=204)

            return redirect('prestamos:devoluciones')

        if es_htmx:
            return render(request, 'pages/prestamos/registrar_devolucion_modal.html', {
                'form': form,
                'solicitud': solicitud,
                'es_modal': True,
            }, status=422)

    return redirect('prestamos:devoluciones')