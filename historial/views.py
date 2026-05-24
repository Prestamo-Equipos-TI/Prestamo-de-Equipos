from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import get_object_or_404, render
from inventario.models import Equipo
from averias.models import ReporteAveria
from prestamos.models import SolicitudPrestamo


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

    context = {
        'active_page': 'historial',
        'content_template': 'pages/historial/usuarios_content.html',
        'usuarios': usuarios,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/historial/usuarios_content.html', context)

    return render(request, 'pages/app_layout.html', context)

@login_required
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
def historial_equipos(request):
    equipos = Equipo.objects.filter(
        activo=True
    ).order_by('nombre')

    context = {
        'active_page': 'historial',
        'content_template': 'pages/historial/equipos_content.html',
        'equipos': equipos,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/historial/equipos_content.html', context)

    return render(request, 'pages/app_layout.html', context)
@login_required
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