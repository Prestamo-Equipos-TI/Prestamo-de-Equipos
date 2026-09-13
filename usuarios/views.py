from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from alertas.models import Alerta
from inventario.models import Equipo
from prestamos.models import SolicitudPrestamo


@login_required
def dashboard(request):
    # Verifica si el usuario tiene alertas no leídas para mostrar badge
    hoy = timezone.localdate()

    context = {
        'active_page': 'dashboard',
        'content_template': 'pages/dashboard_content.html',

        # ==========================================
        # ALERTAS
        # ==========================================

        'tiene_alertas_nuevas': Alerta.objects.filter(
            usuario=request.user,
            leida=False
        ).exists(),

        # ==========================================
        # ESTADÍSTICAS DEL INVENTARIO
        # ==========================================

        'total_equipos': Equipo.objects.filter(
            activo=True
        ).count(),

        'equipos_disponibles': Equipo.objects.filter(
            activo=True,
            estado='disponible'
        ).count(),

        'equipos_prestados': Equipo.objects.filter(
            activo=True,
            estado='prestado'
        ).count(),

        'equipos_reservados': Equipo.objects.filter(
            activo=True,
            estado='reservado'
        ).count(),

        'equipos_averiados': Equipo.objects.filter(
            activo=True,
            estado='averiado'
        ).count(),

        'equipos_mantenimiento': Equipo.objects.filter(
            activo=True,
            estado='mantenimiento'
        ).count(),

        # ==========================================
        # ESTADÍSTICAS DE PRÉSTAMOS
        # ==========================================

        'solicitudes_pendientes': SolicitudPrestamo.objects.filter(
            estado=SolicitudPrestamo.ESTADO_PENDIENTE
        ).count(),

        'prestamos_vencidos': SolicitudPrestamo.objects.filter(
            estado=SolicitudPrestamo.ESTADO_ENTREGADO,
            equipo__estado='prestado',
            fecha_devolucion_estimada__lt=hoy,
            fecha_devolucion_real__isnull=True
        ).count(),
    }

    # ==========================================
    # RESPUESTA HTMX
    # ==========================================

    if request.headers.get('HX-Request'):
        return render(
            request,
            'pages/dashboard_content.html',
            context
        )

    # ==========================================
    # CARGA NORMAL DEL DASHBOARD
    # ==========================================

    return render(
        request,
        'pages/app_layout.html',
        context
    )