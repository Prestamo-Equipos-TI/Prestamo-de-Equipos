from django.db import models
from django.contrib.auth.models import User

from inventario.models import Equipo
from prestamos.models import SolicitudPrestamo


class ReporteAveria(models.Model):
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_EN_REVISION = 'en_revision'
    ESTADO_RESUELTA = 'resuelta'

    ESTADOS = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_EN_REVISION, 'En revisión'),
        (ESTADO_RESUELTA, 'Resuelta'),
    ]

    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.PROTECT,
        related_name='averias'
    )

    solicitud_prestamo = models.ForeignKey(
        SolicitudPrestamo,
        on_delete=models.PROTECT,
        related_name='averias',
        null=True,
        blank=True
    )

    reportado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='averias_reportadas'
    )

    descripcion_falla = models.TextField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_PENDIENTE
    )

    fecha_reporte = models.DateTimeField(auto_now_add=True)

    revisado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='averias_revisadas'
    )

    fecha_revision = models.DateTimeField(
        null=True,
        blank=True
    )

    accion_tomada = models.CharField(
        max_length=150,
        blank=True
    )

    observaciones_revision = models.TextField(
        blank=True
    )

    resuelto_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='averias_resueltas'
    )

    fecha_resolucion = models.DateTimeField(
        null=True,
        blank=True
    )

    observaciones_resolucion = models.TextField(
        blank=True
    )

    def __str__(self):
        return f'{self.equipo.codigo} - {self.get_estado_display()}'