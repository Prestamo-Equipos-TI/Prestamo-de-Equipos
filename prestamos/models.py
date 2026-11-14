from django.db import models
from django.contrib.auth.models import User
from inventario.models import Equipo


class SolicitudPrestamo(models.Model):
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADO = 'aprobado'
    ESTADO_RECHAZADO = 'rechazado'
    ESTADO_ENTREGADO = 'entregado'
    ESTADO_DEVUELTO = 'devuelto'
    ESTADO_CANCELADO = 'cancelado'
    ESTADO_CANCELACION_PENDIENTE = 'cancelacion_pendiente'

    ESTADOS = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADO, 'Aprobado'),
        (ESTADO_RECHAZADO, 'Rechazado'),
        (ESTADO_ENTREGADO, 'Entregado'),
        (ESTADO_DEVUELTO, 'Devuelto'),
        (ESTADO_CANCELADO, 'Cancelado'),
        (ESTADO_CANCELACION_PENDIENTE, 'Cancelación pendiente de devolución'),
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

    fecha_entrega_programada = models.DateField(
    null=True,
    blank=True
    )

    dias_prestamo = models.PositiveIntegerField(
    null=True,
    blank=True
    )

    fecha_entrega_real = models.DateField(
    null=True,
    blank=True
     )

    fecha_devolucion_estimada = models.DateField(
    null=True,
    blank=True
    )

    fecha_devolucion_real = models.DateField(
    null=True,
    blank=True
    )
    alerta_vencimiento_enviada = models.BooleanField(default=False)
    observaciones_entrega = models.TextField(
    blank=True
    )

    observaciones_devolucion = models.TextField(
    blank=True
    )
    

    observaciones = models.TextField(
    blank=True
    )

    estado = models.CharField(
        max_length=30,
        choices=ESTADOS,
        default=ESTADO_PENDIENTE
    )
    aprobado_por = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='solicitudes_aprobadas'
)

    rechazado_por = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='solicitudes_rechazadas'
)

    entregado_por = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='solicitudes_entregadas'
)

    devuelto_por = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='solicitudes_devueltas'
)

    def __str__(self):
        return f'{self.usuario.username} - {self.equipo.nombre}'


class RegistroEstadoSolicitud(models.Model):
    solicitud = models.ForeignKey(
        SolicitudPrestamo, on_delete=models.PROTECT, related_name='transiciones'
    )
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    estado_anterior = models.CharField(max_length=30)
    estado_nuevo = models.CharField(max_length=30)
    motivo = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha', 'pk']

    def get_estado_anterior_display(self):
        return dict(SolicitudPrestamo.ESTADOS).get(self.estado_anterior, self.estado_anterior)

    def get_estado_nuevo_display(self):
        return dict(SolicitudPrestamo.ESTADOS).get(self.estado_nuevo, self.estado_nuevo)


