from django.db import models
from django.contrib.auth.models import User


class Alerta(models.Model):
    TIPO_SISTEMA = 'sistema'
    TIPO_PRESTAMO_APROBADO = 'prestamo_aprobado'
    TIPO_PRESTAMO_RECHAZADO = 'prestamo_rechazado'
    TIPO_PRESTAMO_ENTREGADO = 'prestamo_entregado'

    TIPOS = [
    (TIPO_SISTEMA, 'Sistema'),
    (TIPO_PRESTAMO_APROBADO, 'Préstamo aprobado'),
    (TIPO_PRESTAMO_RECHAZADO, 'Préstamo rechazado'),
    (TIPO_PRESTAMO_ENTREGADO, 'Préstamo entregado'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='alertas'
    )

    titulo = models.CharField(max_length=120)
    mensaje = models.TextField()

    tipo = models.CharField(
        max_length=40,
        choices=TIPOS,
        default=TIPO_SISTEMA
    )

    leida = models.BooleanField(default=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.usuario.username} - {self.titulo}'