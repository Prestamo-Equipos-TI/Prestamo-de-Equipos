from django.utils import timezone

from alertas.models import Alerta
from averias.models import ReporteAveria
from usuarios.models import PerfilUsuario

from .models import SolicitudPrestamo


def estado_equipo_tras_cierre(equipo, condicion='operativo'):
    if SolicitudPrestamo.objects.filter(
        equipo=equipo,
        estado__in=(SolicitudPrestamo.ESTADO_ENTREGADO,
                    SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE),
        fecha_devolucion_real__isnull=True,
    ).exists():
        return 'prestado'
    if equipo.estado in ('averiado', 'mantenimiento'):
        return equipo.estado
    if ReporteAveria.objects.filter(
        equipo=equipo,
        estado__in=(ReporteAveria.ESTADO_PENDIENTE, ReporteAveria.ESTADO_EN_REVISION),
    ).exists():
        return 'averiado'
    if condicion == 'mantenimiento' or not equipo.activo:
        return 'mantenimiento'
    if SolicitudPrestamo.objects.filter(
        equipo=equipo, estado=SolicitudPrestamo.ESTADO_APROBADO,
    ).exists():
        return 'reservado'
    return 'disponible'


def detectar_prestamos_vencidos():
    # Detecta préstamos entregados con fecha de devolución vencida sin alerta previa
    hoy = timezone.localdate()

    prestamos_vencidos = SolicitudPrestamo.objects.select_related(
        'usuario',
        'equipo'
    ).filter(
        estado__in=(SolicitudPrestamo.ESTADO_ENTREGADO,
                    SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE),
        fecha_devolucion_estimada__lt=hoy,
        fecha_devolucion_real__isnull=True,
        alerta_vencimiento_enviada=False
    )

    administradores_ti = PerfilUsuario.objects.filter(
        rol__in=(PerfilUsuario.ROL_ADMIN_TI, PerfilUsuario.ROL_SUPERADMIN)
    ).select_related('user')

    for prestamo in prestamos_vencidos:
        # Notifica al usuario sobre su préstamo vencido
        Alerta.objects.create(
            usuario=prestamo.usuario,
            titulo='Préstamo vencido',
            mensaje=(
                f'El préstamo del equipo {prestamo.equipo.nombre} '
                f'ha vencido y debes gestionar su devolución.'
            ),
            tipo=Alerta.TIPO_SISTEMA
        )

        # Notifica a administradores TI para seguimiento
        for admin in administradores_ti:
            Alerta.objects.create(
                usuario=admin.user,
                titulo='Préstamo vencido detectado',
                mensaje=(
                    f'El usuario {prestamo.usuario.username} tiene vencido '
                    f'el préstamo del equipo {prestamo.equipo.nombre}.'
                ),
                tipo=Alerta.TIPO_SISTEMA
            )

        # Marca alerta como enviada para evitar duplicados
        prestamo.alerta_vencimiento_enviada = True
        prestamo.save(update_fields=['alerta_vencimiento_enviada'])
