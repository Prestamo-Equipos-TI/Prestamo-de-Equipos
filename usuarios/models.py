from django.db import models
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    ROL_ADMIN_TI = 'admin_ti'
    ROL_USUARIO = 'usuario'

    ROLES = [
        (ROL_ADMIN_TI, 'Administrador TI'),
        (ROL_USUARIO, 'Usuario'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )

    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default=ROL_USUARIO
    )

    carnet = models.CharField(
        max_length=30,
        unique=True
    )

    nombre_completo = models.CharField(
        max_length=150
    )

    telefono = models.CharField(
        max_length=20,
        blank=True
    )

    def __str__(self):
        return f'{self.nombre_completo} - {self.get_rol_display()}'