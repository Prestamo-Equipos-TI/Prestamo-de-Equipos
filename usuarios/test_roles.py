from io import StringIO

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from .models import PerfilUsuario, RegistroGestionUsuario


class RolesFuncionalesTest(TestCase):
    def setUp(self):
        self.principal = self.crear('principal', 'superadmin', 'P-1', principal=True)
        self.secundario = self.crear('secundario', 'superadmin', 'S-1')
        self.admin = self.crear('admin', 'admin_ti', 'A-1')
        self.solicitante = self.crear('solicitante', 'usuario', 'U-1')

    def crear(self, username, rol, carnet, principal=False):
        user = User.objects.create_user(username, password='clave-segura-2026')
        PerfilUsuario.objects.create(user=user, rol=rol, carnet=carnet,
                                     nombre_completo=username, es_principal=principal)
        return user

    def datos(self, usuario, rol):
        return {
            'username': usuario.username, 'email': 'nuevo@example.test',
            'nombre_completo': usuario.username, 'carnet': usuario.perfil.carnet,
            'telefono': '', 'rol': rol,
        }

    def test_admin_no_puede_elevar_ni_gestionar_admin(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse('usuario_crear'), {
            **self.datos(self.solicitante, 'superadmin'),
            'username': 'intruso', 'carnet': 'X-1',
        }, HTTP_HX_REQUEST='true')
        self.assertEqual(respuesta.status_code, 422)
        self.assertFalse(User.objects.filter(username='intruso').exists())
        self.assertEqual(self.client.get(reverse('usuario_detalle', args=[self.secundario.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('usuario_editar', args=[self.solicitante.pk]),
                                          self.datos(self.solicitante, 'admin_ti'),
                                          HTTP_HX_REQUEST='true').status_code, 422)
        self.solicitante.perfil.refresh_from_db()
        self.assertEqual(self.solicitante.perfil.rol, 'usuario')

    def test_secundario_gestiona_admin_pero_no_superadmin(self):
        self.client.force_login(self.secundario)
        self.assertContains(self.client.get(reverse('usuarios_lista')), 'admin')
        self.assertEqual(self.client.get(reverse('usuario_detalle', args=[self.principal.pk])).status_code, 404)
        respuesta = self.client.post(reverse('usuario_editar', args=[self.admin.pk]),
                                    self.datos(self.admin, 'usuario'))
        self.assertEqual(respuesta.status_code, 200)
        self.admin.perfil.refresh_from_db()
        self.assertEqual(self.admin.perfil.rol, 'usuario')
        self.assertTrue(RegistroGestionUsuario.objects.filter(
            actor=self.secundario, usuario=self.admin, accion='cambiar_rol',
            rol_anterior='admin_ti', rol_nuevo='usuario').exists())
        respuesta = self.client.post(reverse('usuario_crear'), {
            **self.datos(self.solicitante, 'superadmin'),
            'username': 'otro', 'carnet': 'X-2',
        }, HTTP_HX_REQUEST='true')
        self.assertEqual(respuesta.status_code, 422)

    def test_principal_crea_superadmin_sin_privilegios_tecnicos(self):
        self.client.force_login(self.principal)
        respuesta = self.client.post(reverse('usuario_crear'), {
            **self.datos(self.solicitante, 'superadmin'),
            'username': 'nuevo_super', 'carnet': 'S-2',
        })
        self.assertEqual(respuesta.status_code, 200)
        nuevo = User.objects.get(username='nuevo_super')
        self.assertEqual(nuevo.perfil.rol, 'superadmin')
        self.assertFalse(nuevo.perfil.es_principal)
        self.assertFalse(nuevo.is_staff)
        self.assertFalse(nuevo.is_superuser)
        self.assertEqual(self.client.get(reverse('usuario_detalle', args=[nuevo.pk])).status_code, 200)

    def test_principal_no_se_desactiva_ni_degrada_ni_elimina(self):
        self.client.force_login(self.principal)
        self.assertEqual(self.client.post(reverse('usuario_estado', args=[self.principal.pk]),
                                          {'accion': 'desactivar'}).status_code, 403)
        perfil = self.principal.perfil
        perfil.rol = 'usuario'
        with self.assertRaises(ValidationError):
            perfil.save(update_fields=['rol'])
        self.principal.is_active = False
        with self.assertRaises(ValidationError):
            self.principal.save(update_fields=['is_active'])
        with transaction.atomic():
            with self.assertRaises(ProtectedError):
                perfil.delete()
        self.assertTrue(User.objects.get(pk=self.principal.pk).is_active)

    def test_rutas_administrativas_rechazan_solicitante(self):
        self.client.force_login(self.solicitante)
        rutas = [
            reverse('inventario:crear'), reverse('inventario:lista'),
            reverse('prestamos:admin_inicio'), reverse('prestamos:entregas'),
            reverse('averias:admin_inicio'), reverse('averias:reporte_administrativo'),
            reverse('historial:inicio'),
        ]
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 403)

    def test_rutas_solicitante_rechazan_administrador(self):
        self.client.force_login(self.admin)
        for ruta in (reverse('prestamos:solicitar'), reverse('prestamos:mis_solicitudes'),
                     reverse('averias:reportar')):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 403)

    def test_superusuario_tecnico_sin_rol_no_obtiene_gestion_funcional(self):
        tecnico = User.objects.create_superuser('tecnico', password='clave-segura-2026')
        self.client.force_login(tecnico)
        self.assertEqual(self.client.get(reverse('usuarios_lista')).status_code, 403)
        self.assertEqual(self.client.get(reverse('inventario:crear')).status_code, 403)


class AsignacionPrincipalTest(TestCase):
    def setUp(self):
        self.operador = User.objects.create_superuser('operador', password='clave-segura-2026')
        self.destino = User.objects.create_user('destino', password='clave-segura-2026')
        PerfilUsuario.objects.create(user=self.destino, rol='admin_ti', carnet='A-1',
                                     nombre_completo='Destino')

    def asignar(self, usuario, **extra):
        return call_command('asignar_superadmin_principal', usuario_id=usuario.pk,
                            confirmar_id=usuario.pk, operador_id=self.operador.pk,
                            motivo='Designación aprobada para revisión',
                            stdout=StringIO(), **extra)

    def test_asignacion_explicita_y_transferencia_auditada(self):
        self.asignar(self.destino)
        self.destino.perfil.refresh_from_db()
        self.assertEqual(self.destino.perfil.rol, 'superadmin')
        self.assertTrue(self.destino.perfil.es_principal)
        self.assertFalse(self.destino.is_staff)
        self.assertFalse(self.destino.is_superuser)
        self.assertEqual(RegistroGestionUsuario.objects.filter(
            usuario=self.destino, accion='asignar_principal').count(), 1)
        nuevo = User.objects.create_user('nuevo', password='clave-segura-2026')
        PerfilUsuario.objects.create(user=nuevo, rol='superadmin', carnet='S-1',
                                     nombre_completo='Nuevo')
        with self.assertRaises(CommandError):
            self.asignar(nuevo)
        self.asignar(nuevo, reemplazar=True)
        self.destino.perfil.refresh_from_db()
        nuevo.perfil.refresh_from_db()
        self.assertFalse(self.destino.perfil.es_principal)
        self.assertTrue(nuevo.perfil.es_principal)
        self.assertEqual(PerfilUsuario.objects.filter(es_principal=True).count(), 1)

    def test_requiere_operador_tecnico_y_confirmacion(self):
        with self.assertRaises(CommandError):
            call_command('asignar_superadmin_principal', usuario_id=self.destino.pk,
                         confirmar_id=999, operador_id=self.operador.pk, motivo='Prueba')
        with self.assertRaises(CommandError):
            call_command('asignar_superadmin_principal', usuario_id=self.destino.pk,
                         confirmar_id=self.destino.pk, operador_id=self.destino.pk,
                         motivo='Prueba')
        self.assertFalse(PerfilUsuario.objects.filter(es_principal=True).exists())

    def test_cuenta_tecnica_existente_recibe_perfil_sin_cambiar_flags(self):
        self.asignar(self.operador, carnet='ROOT-1', nombre_completo='Operador')
        self.operador.refresh_from_db()
        self.assertTrue(self.operador.is_staff)
        self.assertTrue(self.operador.is_superuser)
        self.assertTrue(self.operador.perfil.es_principal)
        self.assertEqual(self.operador.perfil.rol, 'superadmin')
