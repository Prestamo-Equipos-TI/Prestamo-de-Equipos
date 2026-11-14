from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from alertas.models import Alerta
from inventario.models import Equipo
from usuarios.models import PerfilUsuario
from .services import detectar_prestamos_vencidos, estado_equipo_tras_cierre
from .forms import SolicitudPrestamoForm
from .forms_cancelacion import CancelarSolicitudForm
from .forms_aprobacion import AprobarSolicitudForm
from .forms_devolucion import RegistrarDevolucionForm
from .forms_entrega import RegistrarEntregaForm
from .models import RegistroEstadoSolicitud, SolicitudPrestamo
from config.reportes import exportar_reporte, fecha
from usuarios.permisos import rol_funcional, solo_gestor_ti, solo_solicitante


@login_required
@solo_solicitante
def solicitar_prestamo_lista(request):
    # Lista equipos disponibles para solicitar préstamo
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
@solo_solicitante
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
            # Evita duplicados: un usuario no puede tener 2 solicitudes pendientes del mismo equipo
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

            # Notifica a administradores TI sobre nueva solicitud
            administradores_ti = PerfilUsuario.objects.filter(
                rol__in=(PerfilUsuario.ROL_ADMIN_TI, PerfilUsuario.ROL_SUPERADMIN)
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
@solo_solicitante
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


def _solicitud_cancelable(request, solicitud_id, bloquear=False):
    rol = rol_funcional(request.user)
    consulta = SolicitudPrestamo.objects.select_related('usuario', 'equipo')
    if bloquear:
        consulta = consulta.select_for_update(of=('self',))
    if rol == PerfilUsuario.ROL_USUARIO:
        consulta = consulta.filter(usuario=request.user, estado=SolicitudPrestamo.ESTADO_PENDIENTE)
    elif rol in (PerfilUsuario.ROL_ADMIN_TI, PerfilUsuario.ROL_SUPERADMIN):
        consulta = consulta.filter(estado__in=(
            SolicitudPrestamo.ESTADO_PENDIENTE,
            SolicitudPrestamo.ESTADO_APROBADO,
            SolicitudPrestamo.ESTADO_ENTREGADO,
        ))
    else:
        return None
    return get_object_or_404(consulta, pk=solicitud_id)


@login_required
@require_http_methods(['GET', 'POST'])
def cancelar_solicitud(request, solicitud_id):
    solicitud = _solicitud_cancelable(request, solicitud_id)
    if solicitud is None:
        return HttpResponseForbidden('No tienes permiso para cancelar solicitudes.')
    form = CancelarSolicitudForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            solicitud = _solicitud_cancelable(request, solicitud_id, bloquear=True)
            equipo = Equipo.objects.select_for_update().get(pk=solicitud.equipo_id)
            anterior = solicitud.estado
            solicitud.estado = (
                SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE
                if anterior == SolicitudPrestamo.ESTADO_ENTREGADO
                else SolicitudPrestamo.ESTADO_CANCELADO
            )
            solicitud.save(update_fields=['estado'])
            RegistroEstadoSolicitud.objects.create(
                solicitud=solicitud, actor=request.user, estado_anterior=anterior,
                estado_nuevo=solicitud.estado, motivo=form.cleaned_data['motivo'],
            )
            if anterior == SolicitudPrestamo.ESTADO_APROBADO:
                equipo.estado = estado_equipo_tras_cierre(equipo)
                equipo.save(update_fields=['estado'])
            titulo = ('Devolución requerida para cancelar' if anterior == SolicitudPrestamo.ESTADO_ENTREGADO
                      else 'Solicitud cancelada')
            if request.user != solicitud.usuario:
                Alerta.objects.create(
                    usuario=solicitud.usuario, titulo=titulo,
                    mensaje=f'{equipo.nombre}: {form.cleaned_data["motivo"]}',
                    tipo=Alerta.TIPO_SISTEMA,
                )
            else:
                for perfil in PerfilUsuario.objects.filter(
                    rol__in=(PerfilUsuario.ROL_ADMIN_TI, PerfilUsuario.ROL_SUPERADMIN),
                    user__is_active=True,
                ).select_related('user'):
                    Alerta.objects.create(
                        usuario=perfil.user, titulo='Solicitud cancelada por solicitante',
                        mensaje=f'{solicitud.usuario.username} canceló {equipo.nombre}: {form.cleaned_data["motivo"]}',
                        tipo=Alerta.TIPO_SISTEMA,
                    )
        if request.headers.get('HX-Request'):
            return HttpResponse(status=204)
        return redirect('prestamos:mis_solicitudes' if request.user == solicitud.usuario
                        else 'prestamos:solicitudes_admin')
    return render(request, 'pages/prestamos/cancelar_solicitud_modal.html', {
        'solicitud': solicitud, 'form': form,
        'es_modal': bool(request.headers.get('HX-Request')),
    }, status=422 if request.method == 'POST' and request.headers.get('HX-Request') else 200)


@login_required
def historial_cancelacion(request, solicitud_id):
    rol = rol_funcional(request.user)
    if rol not in (PerfilUsuario.ROL_USUARIO, PerfilUsuario.ROL_ADMIN_TI,
                   PerfilUsuario.ROL_SUPERADMIN):
        return HttpResponseForbidden('Sin acceso al historial.')
    consulta = SolicitudPrestamo.objects.select_related('equipo', 'usuario')
    if rol == PerfilUsuario.ROL_USUARIO:
        consulta = consulta.filter(usuario=request.user)
    solicitud = get_object_or_404(consulta, pk=solicitud_id)
    return render(request, 'pages/prestamos/historial_cancelacion_modal.html', {
        'solicitud': solicitud,
        'transiciones': solicitud.transiciones.select_related('actor'),
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
@solo_gestor_ti
def solicitudes_admin(request):
    solicitudes = SolicitudPrestamo.objects.select_related(
        'usuario',
        'usuario__perfil',
        'equipo'
    ).order_by('-fecha_solicitud')

    if request.GET.get('export') in ('pdf', 'excel'):
        filas = [(s.usuario.perfil.nombre_completo, s.usuario.perfil.carnet,
                  s.equipo.nombre, s.equipo.codigo, fecha(s.fecha_prestamo),
                  s.get_estado_display(), fecha(s.fecha_solicitud),
                  fecha(s.fecha_devolucion_estimada)) for s in solicitudes]
        return exportar_reporte(request.GET['export'], 'solicitudes', 'Solicitudes de préstamo', [
            ('Solicitudes', ['Solicitante', 'Carnet', 'Equipo', 'Código', 'Fecha solicitada',
                             'Estado', 'Enviada', 'Devolución estimada'], filas),
        ])

    context = {
        'active_page': 'solicitudes_admin',
        'content_template': 'pages/prestamos/solicitudes_admin_content.html',
        'solicitudes': solicitudes,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/prestamos/solicitudes_admin_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
@solo_gestor_ti
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
@solo_gestor_ti
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
@solo_gestor_ti
@transaction.atomic
def confirmar_aprobacion_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_for_update(of=('self',)).select_related(
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
            equipo = Equipo.objects.select_for_update().get(pk=solicitud.equipo_id)
            if not equipo.activo or equipo.estado != 'disponible':
                return HttpResponse('El equipo ya no está disponible.', status=409)
            solicitud.fecha_entrega_programada = form.cleaned_data['fecha_entrega_programada']
            solicitud.dias_prestamo = form.cleaned_data['dias_prestamo']
            solicitud.estado = SolicitudPrestamo.ESTADO_APROBADO
            solicitud.aprobado_por = request.user
            solicitud.save()

            # Cambia estado del equipo a reservado
            equipo.estado = 'reservado'
            equipo.save(update_fields=['estado'])

            # Rechaza automáticamente otras solicitudes pendientes del mismo equipo
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

            # Notifica al solicitante aprobado
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

            # Notifica a los demás solicitantes que fueron rechazados
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
@solo_gestor_ti
@transaction.atomic
def rechazar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_for_update(of=('self',)).select_related(
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
@solo_gestor_ti
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
@solo_gestor_ti
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
@solo_gestor_ti
@transaction.atomic
def confirmar_entrega(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_for_update(of=('self',)).select_related(
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
            equipo = Equipo.objects.select_for_update().get(pk=solicitud.equipo_id)
            if equipo.estado != 'reservado':
                return HttpResponse('El equipo ya no está reservado.', status=409)
            fecha_real = form.cleaned_data['fecha_entrega_real']
            observaciones = form.cleaned_data['observaciones_entrega']

            solicitud.fecha_entrega_real = fecha_real
            # Calcula fecha estimada de devolución sumando días de préstamo
            solicitud.fecha_devolucion_estimada = fecha_real + timedelta(
                days=solicitud.dias_prestamo
            )
            solicitud.observaciones_entrega = observaciones
            solicitud.estado = SolicitudPrestamo.ESTADO_ENTREGADO
            solicitud.entregado_por = request.user
            solicitud.save()

            # Cambia estado del equipo a prestado
            equipo.estado = 'prestado'
            equipo.save(update_fields=['estado'])

            # Notifica al usuario sobre la entrega y fecha estimada de devolución
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
@solo_gestor_ti
def equipos_prestados(request):
    solicitudes = SolicitudPrestamo.objects.select_related(
        'usuario',
        'usuario__perfil',
        'equipo'
    ).filter(
        estado__in=(SolicitudPrestamo.ESTADO_ENTREGADO,
                    SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE),
        fecha_devolucion_real__isnull=True,
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
@solo_gestor_ti
def detalle_prestamo(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_related(
            'usuario',
            'usuario__perfil',
            'equipo'
        ),
        id=solicitud_id,
        estado__in=(SolicitudPrestamo.ESTADO_ENTREGADO,
                    SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE),
        fecha_devolucion_real__isnull=True,
    )

    return render(request, 'pages/prestamos/detalle_prestamo_modal.html', {
        'solicitud': solicitud,
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
@solo_gestor_ti
def devoluciones_lista(request):
    solicitudes = SolicitudPrestamo.objects.select_related(
        'usuario',
        'usuario__perfil',
        'equipo'
    ).filter(
        estado__in=(SolicitudPrestamo.ESTADO_ENTREGADO,
                    SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE),
        fecha_devolucion_real__isnull=True,
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
@solo_gestor_ti
def registrar_devolucion_modal(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_related(
            'usuario',
            'usuario__perfil',
            'equipo'
        ),
        id=solicitud_id,
        estado__in=(SolicitudPrestamo.ESTADO_ENTREGADO,
                    SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE),
        fecha_devolucion_real__isnull=True,
    )

    form = RegistrarDevolucionForm()

    return render(request, 'pages/prestamos/registrar_devolucion_modal.html', {
        'form': form,
        'solicitud': solicitud,
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
@solo_gestor_ti
@transaction.atomic
def confirmar_devolucion(request, solicitud_id):
    solicitud = get_object_or_404(
        SolicitudPrestamo.objects.select_for_update(of=('self',)).select_related(
            'usuario',
            'usuario__perfil',
            'equipo'
        ),
        id=solicitud_id,
        estado__in=(SolicitudPrestamo.ESTADO_ENTREGADO,
                    SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE),
        fecha_devolucion_real__isnull=True,
    )

    es_htmx = request.headers.get('HX-Request')

    if request.method == 'POST':
        form = RegistrarDevolucionForm(request.POST)

        if form.is_valid():
            equipo = Equipo.objects.select_for_update().get(pk=solicitud.equipo_id)
            anterior = solicitud.estado
            solicitud.fecha_devolucion_real = form.cleaned_data['fecha_devolucion_real']
            solicitud.observaciones_devolucion = form.cleaned_data['observaciones_devolucion']
            solicitud.estado = (SolicitudPrestamo.ESTADO_CANCELADO
                                if anterior == SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE
                                else SolicitudPrestamo.ESTADO_DEVUELTO)
            solicitud.devuelto_por = request.user
            solicitud.save()

            equipo.estado = estado_equipo_tras_cierre(equipo, form.cleaned_data['condicion'])
            equipo.save(update_fields=['estado'])
            if anterior == SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE:
                RegistroEstadoSolicitud.objects.create(
                    solicitud=solicitud, actor=request.user,
                    estado_anterior=anterior, estado_nuevo=solicitud.estado,
                    motivo=f'Devolución física registrada. Condición: {form.cleaned_data["condicion"]}.',
                )

            # Notifica al usuario que la devolución fue registrada correctamente
            Alerta.objects.create(
                usuario=solicitud.usuario,
                titulo=('Cancelación completada' if anterior == SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE
                        else 'Equipo devuelto'),
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
