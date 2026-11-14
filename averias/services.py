from prestamos.models import SolicitudPrestamo

from .models import ReporteAveria


def estado_equipo_tras_falsa_alarma(equipo):
    if SolicitudPrestamo.objects.filter(
        equipo=equipo,
        estado__in=(SolicitudPrestamo.ESTADO_ENTREGADO,
                    SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE),
        fecha_devolucion_real__isnull=True,
    ).exists():
        return 'prestado'
    if equipo.estado == 'mantenimiento' or not equipo.activo:
        return 'mantenimiento'
    if ReporteAveria.objects.filter(
        equipo=equipo,
        estado__in=(ReporteAveria.ESTADO_PENDIENTE,
                    ReporteAveria.ESTADO_EN_REVISION),
    ).exists():
        return 'averiado'
    if SolicitudPrestamo.objects.filter(
        equipo=equipo, estado=SolicitudPrestamo.ESTADO_APROBADO,
    ).exists():
        return 'reservado'
    return 'disponible'
