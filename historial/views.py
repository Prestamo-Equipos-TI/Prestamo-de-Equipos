from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import get_object_or_404, render
from inventario.models import Equipo
from averias.models import ReporteAveria
from prestamos.models import SolicitudPrestamo
from config.reportes import exportar_reporte, fecha, solo_admin_ti


@login_required
def historial_inicio(request):
    context = {
        'active_page': 'historial',
        'content_template': 'pages/historial/historial_content.html',
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/historial/historial_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
@solo_admin_ti
def historial_usuarios(request):
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
        resumen = [(u.perfil.nombre_completo, u.perfil.carnet, u.email,
                    u.total_solicitudes, 'Sí' if u.tiene_prestamo_activo else 'No') for u in usuarios]
        solicitudes = SolicitudPrestamo.objects.select_related('usuario__perfil', 'equipo').filter(
            usuario__perfil__rol='usuario').order_by('usuario__perfil__nombre_completo', '-fecha_solicitud')
        movimientos = [(s.usuario.perfil.nombre_completo, s.usuario.perfil.carnet,
                        s.equipo.codigo, fecha(s.fecha_solicitud), fecha(s.fecha_entrega_real),
                        fecha(s.fecha_devolucion_real), s.get_estado_display()) for s in solicitudes]
        return exportar_reporte(request.GET['export'], 'historial_usuarios', 'Historial por usuario', [
            ('Usuarios', ['Usuario', 'Carnet', 'Correo', 'Solicitudes', 'Préstamo activo'], resumen),
            ('Solicitudes', ['Usuario', 'Carnet', 'Equipo', 'Solicitud', 'Entrega',
                             'Devolución', 'Estado'], movimientos),
        ])

    context = {
        'active_page': 'historial',
        'content_template': 'pages/historial/usuarios_content.html',
        'usuarios': usuarios,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/historial/usuarios_content.html', context)

    return render(request, 'pages/app_layout.html', context)

@login_required
@solo_admin_ti
def historial_usuario_detalle(request, usuario_id):
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
        filas = [(s.equipo.nombre, s.equipo.codigo, fecha(s.fecha_solicitud),
                  fecha(s.fecha_prestamo), fecha(s.fecha_entrega_real),
                  fecha(s.fecha_devolucion_estimada), fecha(s.fecha_devolucion_real),
                  s.get_estado_display()) for s in solicitudes]
        return exportar_reporte(request.GET['export'], f'historial_usuario_{usuario.id}',
                                f'Historial de {usuario.perfil.nombre_completo}', [
            ('Solicitudes', ['Equipo', 'Código', 'Solicitud', 'Fecha solicitada', 'Entrega',
                             'Devolución estimada', 'Devolución real', 'Estado'], filas),
        ])

    context = {
        'active_page': 'historial',
        'content_template': 'pages/historial/usuario_detalle_content.html',
        'usuario_historial': usuario,
        'solicitudes': solicitudes,
        'tiene_prestamo_activo': tiene_prestamo_activo,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/historial/usuario_detalle_content.html', context)

    return render(request, 'pages/app_layout.html', context)
@login_required
@solo_admin_ti
def historial_equipos(request):
    equipos = Equipo.objects.filter(
        activo=True
    ).order_by('nombre')

    if request.GET.get('export') in ('pdf', 'excel'):
        resumen = [(e.codigo, e.nombre, e.get_categoria_display(), e.marca,
                    e.get_estado_display()) for e in equipos]
        prestamos = SolicitudPrestamo.objects.select_related('equipo', 'usuario__perfil').filter(
            equipo__activo=True).order_by('equipo__nombre', '-fecha_solicitud')
        uso = [(p.equipo.codigo, p.usuario.perfil.nombre_completo, fecha(p.fecha_solicitud),
                fecha(p.fecha_entrega_real), fecha(p.fecha_devolucion_real),
                p.get_estado_display()) for p in prestamos]
        averias = ReporteAveria.objects.select_related('equipo', 'reportado_por').filter(
            equipo__activo=True).order_by('equipo__nombre', '-fecha_reporte')
        fallas = [(a.equipo.codigo, a.descripcion_falla, fecha(a.fecha_reporte),
                   a.get_estado_display(), a.reportado_por.username if a.reportado_por else 'Sistema')
                  for a in averias]
        return exportar_reporte(request.GET['export'], 'historial_equipos', 'Historial por equipo', [
            ('Equipos', ['Código', 'Equipo', 'Categoría', 'Marca', 'Estado'], resumen),
            ('Préstamos', ['Equipo', 'Usuario', 'Solicitud', 'Entrega', 'Devolución', 'Estado'], uso),
            ('Averías', ['Equipo', 'Descripción', 'Reportada', 'Estado', 'Reportado por'], fallas),
        ])

    context = {
        'active_page': 'historial',
        'content_template': 'pages/historial/equipos_content.html',
        'equipos': equipos,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/historial/equipos_content.html', context)

    return render(request, 'pages/app_layout.html', context)
@login_required
@solo_admin_ti
def historial_equipo_detalle(request, equipo_id):
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
        uso = [(p.usuario.perfil.nombre_completo, fecha(p.fecha_solicitud),
                fecha(p.fecha_entrega_real), fecha(p.fecha_devolucion_estimada),
                fecha(p.fecha_devolucion_real), p.get_estado_display()) for p in prestamos]
        fallas = [(a.reportado_por.username if a.reportado_por else 'Sistema',
                   a.descripcion_falla, fecha(a.fecha_reporte), a.get_estado_display(),
                   a.revisado_por.username if a.revisado_por else '-',
                   a.resuelto_por.username if a.resuelto_por else '-') for a in averias]
        return exportar_reporte(request.GET['export'], f'historial_equipo_{equipo.id}',
                                f'Historial de {equipo.nombre} ({equipo.codigo})', [
            ('Préstamos', ['Usuario', 'Solicitud', 'Entrega', 'Devolución estimada',
                           'Devolución real', 'Estado'], uso),
            ('Averías', ['Reportado por', 'Descripción', 'Reportada', 'Estado',
                         'Revisado por', 'Resuelto por'], fallas),
        ])

    context = {
        'active_page': 'historial',
        'content_template': 'pages/historial/equipo_detalle_content.html',
        'equipo_historial': equipo,
        'prestamos': prestamos,
        'averias': averias,
        'ultimo_prestamo': ultimo_prestamo,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/historial/equipo_detalle_content.html', context)

    return render(request, 'pages/app_layout.html', context)