from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import PerfilUsuario
from .admin_site import AdminEmergenciaSite


class AccesoAdminEmergenciaTest(TestCase):
    def setUp(self):
        self.tecnico = User.objects.create_superuser(
            'tecnico', password='Clave-tecnica-segura-2026',
        )
        self.principal = User.objects.create_superuser(
            'principal', password='Clave-principal-segura-2026',
        )
        PerfilUsuario.objects.create(
            user=self.principal, rol=PerfilUsuario.ROL_SUPERADMIN,
            es_principal=True, carnet='P-1', nombre_completo='Principal',
        )
        self.funcional = User.objects.create_user(
            'funcional', password='Clave-funcional-segura-2026',
        )
        PerfilUsuario.objects.create(
            user=self.funcional, rol=PerfilUsuario.ROL_SUPERADMIN,
            carnet='S-1', nombre_completo='Superadministrador funcional',
        )
        self.admin_ti = User.objects.create_user(
            'admin_ti', password='Clave-admin-segura-2026',
        )
        PerfilUsuario.objects.create(
            user=self.admin_ti, rol=PerfilUsuario.ROL_ADMIN_TI,
            carnet='A-1', nombre_completo='Administrador TI',
        )
        self.solicitante = User.objects.create_user(
            'solicitante', password='Clave-usuario-segura-2026',
        )
        PerfilUsuario.objects.create(
            user=self.solicitante, rol=PerfilUsuario.ROL_USUARIO,
            carnet='U-1', nombre_completo='Solicitante',
        )

    def test_sitio_admin_sigue_disponible_para_cuentas_tecnicas(self):
        self.assertIsInstance(admin.site, AdminEmergenciaSite)
        for usuario in (self.tecnico, self.principal):
            with self.subTest(usuario=usuario.username):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)
                self.assertEqual(self.client.get(reverse('admin:usuarios_perfilusuario_changelist')).status_code, 200)
                self.assertEqual(self.client.get(reverse('admin:auth_user_changelist')).status_code, 200)

    def test_roles_funcionales_no_conceden_entrada(self):
        for usuario in (self.funcional, self.admin_ti, self.solicitante):
            with self.subTest(usuario=usuario.username):
                self.client.force_login(usuario)
                for url in (reverse('admin:index'), reverse('admin:auth_user_changelist')):
                    respuesta = self.client.get(url)
                    self.assertEqual(respuesta.status_code, 302)
                    self.assertIn('/admin/login/', respuesta['Location'])

    def test_staff_sin_superuser_no_puede_entrar_ni_autenticarse_en_admin(self):
        staff = User.objects.create_user('staff', password='Clave-staff-segura-2026',
                                         is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 302)
        self.client.logout()
        respuesta = self.client.post(reverse('admin:login'), {
            'username': 'staff', 'password': 'Clave-staff-segura-2026',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'cuentas técnicas de emergencia')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_superuser_sin_staff_e_inactivo_no_entran(self):
        self.tecnico.is_staff = False
        self.tecnico.save(update_fields=['is_staff'])
        self.client.force_login(self.tecnico)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 302)
        self.client.logout()
        inactivo = User.objects.create_superuser('inactivo', password='Clave-inactiva-segura-2026')
        inactivo.is_active = False
        inactivo.save(update_fields=['is_active'])
        self.client.force_login(inactivo)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 302)

    def test_login_tecnico_y_recuperacion_por_nuevo_superusuario(self):
        self.assertEqual(self.client.get(reverse('admin:login')).status_code, 200)
        respuesta = self.client.post(reverse('admin:login'), {
            'username': 'tecnico', 'password': 'Clave-tecnica-segura-2026',
        })
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)
