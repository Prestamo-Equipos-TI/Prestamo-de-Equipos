from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from .models import PerfilUsuario


@receiver(pre_save, sender=PerfilUsuario)
def proteger_rol_principal(sender, instance, **kwargs):
    if instance.pk and PerfilUsuario.objects.filter(pk=instance.pk, es_principal=True).exists():
        if not instance.es_principal or instance.rol != PerfilUsuario.ROL_SUPERADMIN:
            raise ValidationError('No se puede degradar al superadministrador principal.')


@receiver(pre_save, sender=User)
def proteger_cuenta_principal(sender, instance, **kwargs):
    if instance.pk and not instance.is_active:
        if PerfilUsuario.objects.filter(user_id=instance.pk, es_principal=True).exists():
            raise ValidationError('No se puede desactivar al superadministrador principal.')


@receiver(pre_delete, sender=PerfilUsuario)
def proteger_eliminacion_principal(sender, instance, **kwargs):
    if instance.es_principal:
        raise ProtectedError('No se puede eliminar el perfil principal.', [instance])
