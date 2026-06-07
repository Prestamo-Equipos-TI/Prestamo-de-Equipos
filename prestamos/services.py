from django.utils import timezone

from alertas.models import Alerta
from usuarios.models import PerfilUsuario

from .models import SolicitudPrestamo


def detectar_prestamos_vencidos():
    # Detecta préstamos entregados con fecha de devolución vencida sin alerta previa
    hoy = timezone.localdate()

    prestamos_vencidos = SolicitudPrestamo.objects.select_related(
        'usuario',
        'equipo'
    ).filter(
        estado=SolicitudPrestamo.ESTADO_ENTREGADO,
        equipo__estado='prestado',
        fecha_devolucion_estimada__lt=hoy,
        fecha_devolucion_real__isnull=True,
        alerta_vencimiento_enviada=False
    )

    administradores_ti = PerfilUsuario.objects.filter(
        rol=PerfilUsuario.ROL_ADMIN_TI
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
