from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from inventario.models import Equipo
from averias.models import ReporteAveria
from prestamos.models import SolicitudPrestamo
from config.reportes import exportar_reporte, filtrar_periodo, periodo_reporte
from usuarios.permisos import solo_gestor_ti


@login_required
@solo_gestor_ti
def historial_inicio(request):
    context = {
        'active_page': 'historial',
        'content_template': 'pages/historial/historial_content.html',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/historial/historial_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
@solo_gestor_ti
def historial_usuarios(request):
    desde, hasta, error_periodo = periodo_reporte(request)
    prestamos_activos = SolicitudPrestamo.objects.filter(
        usuario=OuterRef('pk'),
        estado=SolicitudPrestamo.ESTADO_ENTREGADO,
        equipo__estado='prestado'
    )

    usuarios = User.objects.select_related(
        'perfil'
    ).annotate(
        total_solicitudes=Count('solicitudes_prestamo'),
        tiene_prestamo_activo=Exists(prestamos_activos)
    ).filter(
        perfil__rol='usuario'
    ).order_by('perfil__nombre_completo')

    if request.GET.get('export') in ('pdf', 'excel'):
        if error_periodo:
            return HttpResponse(error_periodo, status=400)
        solicitudes = filtrar_periodo(SolicitudPrestamo.objects.select_related(
            'usuario__perfil', 'equipo').filter(usuario__perfil__rol='usuario'),
            'fecha_solicitud', desde, hasta).order_by('usuario__perfil__nombre_completo', '-fecha_solicitud')
        if desde:
            usuarios = usuarios.filter(pk__in=solicitudes.values('usuario_id')).annotate(
                solicitudes_periodo=Count('solicitudes_prestamo', filter=Q(
                    solicitudes_prestamo__fecha_solicitud__date__range=(desde, hasta))))
        resumen = [(u.perfil.nombre_completo, u.perfil.carnet, u.email,
                    u.solicitudes_periodo if desde else u.total_solicitudes,
                    'Sí' if u.tiene_prestamo_activo else 'No') for u in usuarios]
        movimientos = [(s.usuario.perfil.nombre_completo, s.usuario.perfil.carnet,
                        s.equipo.codigo, s.fecha_solicitud, s.fecha_entrega_real,
                        s.fecha_devolucion_real, s.get_estado_display()) for s in solicitudes]
        return exportar_reporte(request.GET['export'], 'historial_usuarios', 'Historial por usuario', [
            ('Usuarios', ['Usuario', 'Carnet', 'Correo', 'Solicitudes', 'Préstamo activo'], resumen),
            ('Solicitudes', ['Usuario', 'Carnet', 'Equipo', 'Solicitud', 'Entrega',
                             'Devolución', 'Estado'], movimientos),
        ], usuario=request.user, desde=desde, hasta=hasta)

    context = {
        'active_page': 'historial',
        'content_template': 'pages/historial/usuarios_content.html',
        'usuarios': usuarios,
        'fecha_inicio': request.GET.get('fecha_inicio', ''),
        'fecha_fin': request.GET.get('fecha_fin', ''),
        'error_periodo': error_periodo,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/historial/usuarios_content.html', context)

    return render(request, 'pages/app_layout.html', context)

@login_required
@solo_gestor_ti
def historial_usuario_detalle(request, usuario_id):
    desde, hasta, error_periodo = periodo_reporte(request)
    usuario = get_object_or_404(
        User.objects.select_related('perfil'),
        id=usuario_id,
        perfil__rol='usuario'
    )

    solicitudes = SolicitudPrestamo.objects.select_related(
        'equipo'
    ).filter(
        usuario=usuario
    ).order_by('-fecha_solicitud')

    tiene_prestamo_activo = solicitudes.filter(
        estado=SolicitudPrestamo.ESTADO_ENTREGADO,
        equipo__estado='prestado'
    ).exists()

    if request.GET.get('export') in ('pdf', 'excel'):
        if error_periodo:
            return HttpResponse(error_periodo, status=400)
        solicitudes = filtrar_periodo(solicitudes, 'fecha_solicitud', desde, hasta)
        filas = [(s.equipo.nombre, s.equipo.codigo, s.fecha_solicitud,
                  s.fecha_prestamo, s.fecha_entrega_real,
                  s.fecha_devolucion_estimada, s.fecha_devolucion_real,
                  s.get_estado_display()) for s in solicitudes]
        return exportar_reporte(request.GET['export'], f'historial_usuario_{usuario.id}',
                                f'Historial de {usuario.perfil.nombre_completo}', [
            ('Solicitudes', ['Equipo', 'Código', 'Solicitud', 'Fecha solicitada', 'Entrega',
                             'Devolución estimada', 'Devolución real', 'Estado'], filas),
        ], usuario=request.user, desde=desde, hasta=hasta, filtros={'Usuario': usuario.perfil.nombre_completo})

    context = {
        'active_page': 'historial',
        'content_template': 'pages/historial/usuario_detalle_content.html',
        'usuario_historial': usuario,
        'solicitudes': solicitudes,
        'tiene_prestamo_activo': tiene_prestamo_activo,
        'fecha_inicio': request.GET.get('fecha_inicio', ''),
        'fecha_fin': request.GET.get('fecha_fin', ''),
        'error_periodo': error_periodo,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/historial/usuario_detalle_content.html', context)

    return render(request, 'pages/app_layout.html', context)
@login_required
@solo_gestor_ti
def historial_equipos(request):
    desde, hasta, error_periodo = periodo_reporte(request)
    equipos = Equipo.objects.filter(
        activo=True
    ).order_by('nombre')

    if request.GET.get('export') in ('pdf', 'excel'):
        if error_periodo:
            return HttpResponse(error_periodo, status=400)
        prestamos = filtrar_periodo(SolicitudPrestamo.objects.select_related(
            'equipo', 'usuario__perfil').filter(equipo__activo=True),
            'fecha_solicitud', desde, hasta).order_by('equipo__nombre', '-fecha_solicitud')
        averias = filtrar_periodo(ReporteAveria.objects.select_related(
            'equipo', 'reportado_por').filter(equipo__activo=True),
            'fecha_reporte', desde, hasta).order_by('equipo__nombre', '-fecha_reporte')
        if desde:
            equipos = equipos.filter(pk__in=set(prestamos.values_list('equipo_id', flat=True)) |
                                     set(averias.values_list('equipo_id', flat=True)))
        resumen = [(e.codigo, e.nombre, e.get_categoria_display(), e.marca,
                    e.get_estado_display()) for e in equipos]
        uso = [(p.equipo.codigo, p.usuario.perfil.nombre_completo, p.fecha_solicitud,
                p.fecha_entrega_real, p.fecha_devolucion_real,
                p.get_estado_display()) for p in prestamos]
        fallas = [(a.equipo.codigo, a.descripcion_falla, a.fecha_reporte,
                   a.get_estado_display(), a.reportado_por.username if a.reportado_por else 'Sistema')
                  for a in averias]
        return exportar_reporte(request.GET['export'], 'historial_equipos', 'Historial por equipo', [
            ('Equipos', ['Código', 'Equipo', 'Categoría', 'Marca', 'Estado'], resumen),
            ('Préstamos', ['Equipo', 'Usuario', 'Solicitud', 'Entrega', 'Devolución', 'Estado'], uso),
            ('Averías', ['Equipo', 'Descripción', 'Reportada', 'Estado', 'Reportado por'], fallas),
        ], usuario=request.user, desde=desde, hasta=hasta)

    context = {
        'active_page': 'historial',
        'content_template': 'pages/historial/equipos_content.html',
        'equipos': equipos,
        'fecha_inicio': request.GET.get('fecha_inicio', ''),
        'fecha_fin': request.GET.get('fecha_fin', ''),
        'error_periodo': error_periodo,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/historial/equipos_content.html', context)

    return render(request, 'pages/app_layout.html', context)
@login_required
@solo_gestor_ti
def historial_equipo_detalle(request, equipo_id):
    desde, hasta, error_periodo = periodo_reporte(request)
    equipo = get_object_or_404(
        Equipo,
        id=equipo_id,
        activo=True
    )

    prestamos = SolicitudPrestamo.objects.select_related(
        'usuario',
        'usuario__perfil'
    ).filter(
        equipo=equipo
    ).order_by('-fecha_solicitud')

    averias = ReporteAveria.objects.select_related(
        'reportado_por',
        'reportado_por__perfil',
        'revisado_por',
        'resuelto_por'
    ).filter(
        equipo=equipo
    ).order_by('-fecha_reporte')

    ultimo_prestamo = prestamos.first()

    if request.GET.get('export') in ('pdf', 'excel'):
        if error_periodo:
            return HttpResponse(error_periodo, status=400)
        prestamos = filtrar_periodo(prestamos, 'fecha_solicitud', desde, hasta)
        averias = filtrar_periodo(averias, 'fecha_reporte', desde, hasta)
        uso = [(p.usuario.perfil.nombre_completo, p.fecha_solicitud,
                p.fecha_entrega_real, p.fecha_devolucion_estimada,
                p.fecha_devolucion_real, p.get_estado_display()) for p in prestamos]
        fallas = [(a.reportado_por.username if a.reportado_por else 'Sistema',
                   a.descripcion_falla, a.fecha_reporte, a.get_estado_display(),
                   a.revisado_por.username if a.revisado_por else '-',
                   a.resuelto_por.username if a.resuelto_por else '-') for a in averias]
        return exportar_reporte(request.GET['export'], f'historial_equipo_{equipo.id}',
                                f'Historial de {equipo.nombre} ({equipo.codigo})', [
            ('Préstamos', ['Usuario', 'Solicitud', 'Entrega', 'Devolución estimada',
                           'Devolución real', 'Estado'], uso),
            ('Averías', ['Reportado por', 'Descripción', 'Reportada', 'Estado',
                         'Revisado por', 'Resuelto por'], fallas),
        ], usuario=request.user, desde=desde, hasta=hasta, filtros={'Equipo': equipo.codigo})

    context = {
        'active_page': 'historial',
        'content_template': 'pages/historial/equipo_detalle_content.html',
        'equipo_historial': equipo,
        'prestamos': prestamos,
        'averias': averias,
        'ultimo_prestamo': ultimo_prestamo,
        'fecha_inicio': request.GET.get('fecha_inicio', ''),
        'fecha_fin': request.GET.get('fecha_fin', ''),
        'error_periodo': error_periodo,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/historial/equipo_detalle_content.html', context)

    return render(request, 'pages/app_layout.html', context)
