from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from usuarios.models import PerfilUsuario, RegistroGestionUsuario


class Command(BaseCommand):
    help = 'Designa explícitamente al superadministrador principal por ID; permite recuperación auditada.'

    def add_arguments(self, parser):
        parser.add_argument('--usuario-id', type=int, required=True)
        parser.add_argument('--confirmar-id', type=int, required=True)
        parser.add_argument('--operador-id', type=int, required=True)
        parser.add_argument('--motivo', required=True)
        parser.add_argument('--carnet')
        parser.add_argument('--nombre-completo')
        parser.add_argument('--reemplazar', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        usuario_id = options['usuario_id']
        if usuario_id != options['confirmar_id']:
            raise CommandError('La confirmación no coincide con el ID de usuario.')
        motivo = options['motivo'].strip()
        if not motivo or len(motivo) > 255:
            raise CommandError('Indica un motivo de hasta 255 caracteres.')
        operador = User.objects.select_for_update().filter(pk=options['operador_id']).first()
        if not operador or not operador.is_active or not operador.is_superuser:
            raise CommandError('El operador debe ser un superusuario técnico activo.')
        usuario = User.objects.select_for_update().filter(pk=usuario_id).first()
        if not usuario or not usuario.is_active:
            raise CommandError('El usuario principal debe existir y estar activo.')

        anterior = PerfilUsuario.objects.select_for_update().filter(es_principal=True).first()
        if anterior and anterior.user_id == usuario_id:
            raise CommandError('Esta cuenta ya es la principal.')
        if anterior and not options['reemplazar']:
            raise CommandError('Ya existe principal. Usa --reemplazar para transferirlo explícitamente.')

        perfil = PerfilUsuario.objects.select_for_update().filter(user=usuario).first()
        if perfil is None:
            if not options['carnet'] or not options['nombre_completo']:
                raise CommandError('La cuenta no tiene perfil: indica --carnet y --nombre-completo.')
            if len(options['carnet']) > 30 or len(options['nombre_completo']) > 150:
                raise CommandError('El carnet o el nombre completo supera el límite permitido.')
            if PerfilUsuario.objects.filter(carnet=options['carnet']).exists():
                raise CommandError('El carnet ya está registrado.')
            perfil = PerfilUsuario.objects.create(
                user=usuario, carnet=options['carnet'],
                nombre_completo=options['nombre_completo'],
            )

        rol_anterior = perfil.rol
        if anterior:
            PerfilUsuario.objects.filter(pk=anterior.pk).update(es_principal=False)
            RegistroGestionUsuario.objects.create(
                actor=operador, usuario=anterior.user, accion='asignar_principal',
                rol_anterior=anterior.rol, rol_nuevo=anterior.rol,
                motivo=f'Principal transferido a usuario ID {usuario_id}: {motivo}'[:255],
            )
        PerfilUsuario.objects.filter(pk=perfil.pk).update(
            rol=PerfilUsuario.ROL_SUPERADMIN, es_principal=True,
        )
        if rol_anterior != PerfilUsuario.ROL_SUPERADMIN:
            RegistroGestionUsuario.objects.create(
                actor=operador, usuario=usuario, accion='cambiar_rol',
                rol_anterior=rol_anterior, rol_nuevo=PerfilUsuario.ROL_SUPERADMIN,
                motivo=motivo,
            )
        RegistroGestionUsuario.objects.create(
            actor=operador, usuario=usuario, accion='asignar_principal',
            rol_anterior=rol_anterior, rol_nuevo=PerfilUsuario.ROL_SUPERADMIN,
            motivo=motivo,
        )
        self.stdout.write(self.style.SUCCESS(f'Principal asignado al usuario ID {usuario_id}.'))
