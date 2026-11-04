import re
from html import unescape

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import PerfilUsuario, RegistroGestionUsuario


class GestionSolicitantesTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('adminqa', password='clave-admin')
        PerfilUsuario.objects.create(
            user=self.admin, rol=PerfilUsuario.ROL_ADMIN_TI,
            carnet='ADM-1', nombre_completo='Admin QA',
        )
        self.solicitante = User.objects.create_user(
            'solicitanteqa', email='solicitante@example.test', password='clave-original',
        )
        PerfilUsuario.objects.create(
            user=self.solicitante, rol=PerfilUsuario.ROL_USUARIO,
            carnet='USR-1', nombre_completo='Solicitante QA',
        )
        self.otro_admin = User.objects.create_user('otroadministrador', password='clave-admin')
        PerfilUsuario.objects.create(
            user=self.otro_admin, rol=PerfilUsuario.ROL_ADMIN_TI,
            carnet='ADM-2', nombre_completo='Otro administrador',
        )
        self.client.force_login(self.admin)

    def datos(self, **cambios):
        return {
            'username': 'nuevoqa',
            'email': 'nuevo@example.test',
            'nombre_completo': 'Nuevo Solicitante',
            'carnet': 'USR-2',
            'telefono': '12345678',
            **cambios,
        }

    def clave_mostrada(self, respuesta):
        texto = respuesta.content.decode()
        return unescape(re.search(r'id="clave-generada"[^>]*value="([^"]+)"', texto).group(1))

    def test_listado_busqueda_y_modales_htmx(self):
        lista = reverse('usuarios_lista')
        respuesta = self.client.get(lista)
        self.assertContains(respuesta, 'Solicitante QA')
        self.assertNotContains(respuesta, 'Otro administrador')
        parcial = self.client.get(lista, {'q': 'USR-1', 'partial': 'tabla'}, HTTP_HX_REQUEST='true')
        self.assertContains(parcial, 'Solicitante QA')
        self.assertNotContains(parcial, 'dashboard-layout')
        self.assertContains(self.client.get(reverse('usuario_crear'), HTTP_HX_REQUEST='true'), 'Registrar solicitante')
        self.assertContains(
            self.client.get(reverse('usuario_detalle', args=[self.solicitante.pk]), HTTP_HX_REQUEST='true'),
            'Solicitante QA',
        )

    def test_crear_valida_duplicados_y_registra_actor(self):
        url = reverse('usuario_crear')
        for cambio in (
            {'username': 'SOLICITANTEQA'},
            {'username': 'usuario con espacios'},
            {'email': 'SOLICITANTE@example.test'},
            {'carnet': 'usr-1'},
        ):
            with self.subTest(cambio=cambio):
                respuesta = self.client.post(url, self.datos(**cambio), HTTP_HX_REQUEST='true')
                self.assertEqual(respuesta.status_code, 422)
        self.assertFalse(User.objects.filter(username='nuevoqa').exists())
        respuesta = self.client.post(url, self.datos(), HTTP_HX_REQUEST='true')
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('no-store', respuesta['Cache-Control'])
        self.assertContains(respuesta, 'hx-history="false"')
        creado = User.objects.get(username='nuevoqa')
        self.assertFalse(creado.is_staff)
        self.assertFalse(creado.is_superuser)
        self.assertEqual(creado.perfil.rol, PerfilUsuario.ROL_USUARIO)
        self.assertTrue(creado.perfil.debe_cambiar_clave)
        self.assertTrue(creado.check_password(self.clave_mostrada(respuesta)))
        registro = RegistroGestionUsuario.objects.get(usuario=creado)
        self.assertEqual((registro.actor, registro.accion), (self.admin, 'crear'))
        self.assertIsNotNone(registro.fecha)

    def test_editar_y_cambiar_estado_preserva_historial(self):
        editar = reverse('usuario_editar', args=[self.solicitante.pk])
        respuesta = self.client.post(
            editar,
            self.datos(username='solicitanteqa', email='editado@example.test', carnet='USR-1'),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(respuesta.status_code, 200)
        self.solicitante.refresh_from_db()
        self.assertEqual(self.solicitante.email, 'editado@example.test')
        self.assertTrue(self.solicitante.check_password('clave-original'))
        estado = reverse('usuario_estado', args=[self.solicitante.pk])
        self.assertEqual(self.client.get(estado).status_code, 405)
        self.assertEqual(self.client.post(estado, {'accion': 'desactivar'}, HTTP_HX_REQUEST='true').status_code, 204)
        self.solicitante.refresh_from_db()
        self.assertFalse(self.solicitante.is_active)
        self.assertEqual(self.client.post(estado, {'accion': 'desactivar'}).status_code, 400)
        self.assertEqual(self.client.post(estado, {'accion': 'activar'}).status_code, 302)
        self.solicitante.refresh_from_db()
        self.assertTrue(self.solicitante.is_active)
        self.assertEqual(
            list(RegistroGestionUsuario.objects.filter(usuario=self.solicitante).values_list('accion', flat=True)),
            ['activar', 'desactivar', 'editar'],
        )

    def test_restablecer_clave_muestra_nueva_una_sola_vez(self):
        url = reverse('usuario_restablecer_clave', args=[self.solicitante.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        respuesta = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertEqual(respuesta.status_code, 200)
        self.solicitante.refresh_from_db()
        self.assertFalse(self.solicitante.check_password('clave-original'))
        self.assertTrue(self.solicitante.check_password(self.clave_mostrada(respuesta)))
        self.assertTrue(self.solicitante.perfil.debe_cambiar_clave)
        self.assertIn('no-store', respuesta['Cache-Control'])
        self.assertEqual(
            RegistroGestionUsuario.objects.get(usuario=self.solicitante).accion,
            'restablecer_clave',
        )

    def test_solicitante_puede_cambiar_su_propia_clave(self):
        self.client.force_login(self.solicitante)
        url = reverse('cambiar_clave')
        respuesta = self.client.post(url, {
            'old_password': 'clave-original',
            'new_password1': 'Una-clave-nueva-larga-2026',
            'new_password2': 'Una-clave-nueva-larga-2026',
        })
        self.assertRedirects(respuesta, url)
        self.solicitante.refresh_from_db()
        self.assertTrue(self.solicitante.check_password('Una-clave-nueva-larga-2026'))
        self.assertTrue(self.client.get(url).wsgi_request.user.is_authenticated)

    def test_clave_temporal_exige_cambio_antes_de_entrar(self):
        respuesta = self.client.post(
            reverse('usuario_restablecer_clave', args=[self.solicitante.pk]),
            HTTP_HX_REQUEST='true',
        )
        clave_temporal = self.clave_mostrada(respuesta)
        self.solicitante.refresh_from_db()
        self.client.force_login(self.solicitante)
        cambio = reverse('cambiar_clave')
        self.assertRedirects(self.client.get(reverse('dashboard')), cambio)
        parcial = self.client.get(reverse('alertas:lista'), HTTP_HX_REQUEST='true')
        self.assertEqual(parcial.status_code, 204)
        self.assertEqual(parcial['HX-Redirect'], cambio)
        self.assertEqual(self.client.get(cambio).status_code, 200)
        respuesta = self.client.post(cambio, {
            'old_password': clave_temporal,
            'new_password1': 'Otra-clave-segura-larga-2026',
            'new_password2': 'Otra-clave-segura-larga-2026',
        })
        self.assertRedirects(respuesta, cambio)
        self.solicitante.refresh_from_db()
        self.assertFalse(self.solicitante.perfil.debe_cambiar_clave)
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)

    def test_no_gestiona_administradores_ni_cuentas_tecnicas(self):
        tecnico = User.objects.create_superuser('tecnicoqa', password='clave-tecnica')
        for usuario in (self.otro_admin, tecnico):
            with self.subTest(usuario=usuario.username):
                self.assertEqual(self.client.get(reverse('usuario_detalle', args=[usuario.pk])).status_code, 404)
                self.assertEqual(self.client.post(reverse('usuario_editar', args=[usuario.pk]), self.datos()).status_code, 404)
                self.assertEqual(self.client.post(reverse('usuario_estado', args=[usuario.pk]), {'accion': 'desactivar'}).status_code, 404)
                self.assertEqual(self.client.post(reverse('usuario_restablecer_clave', args=[usuario.pk])).status_code, 404)
        self.assertTrue(self.otro_admin.is_active)
        self.assertTrue(tecnico.is_active)

    def test_solicitante_y_anonimo_no_acceden_a_ninguna_accion(self):
        rutas = [
            ('get', reverse('usuarios_lista')),
            ('get', reverse('usuario_crear')),
            ('post', reverse('usuario_crear')),
            ('get', reverse('usuario_detalle', args=[self.solicitante.pk])),
            ('get', reverse('usuario_editar', args=[self.solicitante.pk])),
            ('post', reverse('usuario_editar', args=[self.solicitante.pk])),
            ('post', reverse('usuario_estado', args=[self.solicitante.pk])),
            ('post', reverse('usuario_restablecer_clave', args=[self.solicitante.pk])),
        ]
        self.client.force_login(self.solicitante)
        for metodo, ruta in rutas:
            with self.subTest(metodo=metodo, ruta=ruta):
                self.assertEqual(getattr(self.client, metodo)(ruta).status_code, 403)
        self.client.logout()
        for metodo, ruta in rutas:
            with self.subTest(metodo=metodo, ruta=ruta):
                self.assertEqual(getattr(self.client, metodo)(ruta).status_code, 302)
        self.assertEqual(RegistroGestionUsuario.objects.count(), 0)
