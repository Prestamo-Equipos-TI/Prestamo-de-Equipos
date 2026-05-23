from django.db import models
from django.contrib.auth.models import User
from inventario.models import Equipo


class SolicitudPrestamo(models.Model):
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADO = 'aprobado'
    ESTADO_RECHAZADO = 'rechazado'

    ESTADOS = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADO, 'Aprobado'),
        (ESTADO_RECHAZADO, 'Rechazado'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='solicitudes_prestamo'
    )

    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.PROTECT,
        related_name='solicitudes_prestamo'
    )

    fecha_solicitud = models.DateTimeField(
        auto_now_add=True
    )

    fecha_prestamo = models.DateField()

    observaciones = models.TextField(
        blank=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_PENDIENTE
    )

    def __str__(self):
        return f'{self.usuario.username} - {self.equipo.nombre}'


