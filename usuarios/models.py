from django.db import models
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    ROL_ADMIN_TI = 'admin_ti'
    ROL_USUARIO = 'usuario'
    ROL_SUPERADMIN = 'superadmin'

    ROLES = [
        (ROL_ADMIN_TI, 'Administrador TI'),
        (ROL_USUARIO, 'Usuario'),
        (ROL_SUPERADMIN, 'Superadministrador'),
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
    debe_cambiar_clave = models.BooleanField(default=False)
    es_principal = models.BooleanField(default=False, editable=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(es_principal=False) | models.Q(rol='superadmin'),
                name='principal_requiere_rol_superadmin',
            ),
            models.UniqueConstraint(
                fields=['es_principal'],
                condition=models.Q(es_principal=True),
                name='un_solo_superadmin_principal',
            ),
        ]

    def __str__(self):
        return f'{self.nombre_completo} - {self.get_rol_display()}'


class RegistroGestionUsuario(models.Model):
    ACCIONES = [
        ('crear', 'Crear'),
        ('editar', 'Editar'),
        ('activar', 'Activar'),
        ('desactivar', 'Desactivar'),
        ('restablecer_clave', 'Restablecer contraseña'),
        ('cambiar_rol', 'Cambiar rol'),
        ('asignar_principal', 'Asignar principal'),
    ]

    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='gestiones_realizadas')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='gestiones_recibidas')
    accion = models.CharField(max_length=20, choices=ACCIONES)
    rol_anterior = models.CharField(max_length=20, blank=True)
    rol_nuevo = models.CharField(max_length=20, blank=True)
    motivo = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
