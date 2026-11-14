import json
from io import BytesIO
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

from alertas.models import Alerta
from inventario.models import Equipo
from usuarios.models import PerfilUsuario


CARACTERES = 'áéíóúÁÉÍÓÚñÑü¿¡'


class UnicodeExtremoAExtremoTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin_utf8', password='Clave-segura-2026')
        PerfilUsuario.objects.create(
            user=self.admin, rol=PerfilUsuario.ROL_ADMIN_TI,
            carnet='ADM-UTF8', nombre_completo='Administrador',
        )
        self.client.force_login(self.admin)

    def test_equipo_crear_editar_listar_buscar_y_exportar_unicode(self):
        datos = {
            'codigo': 'EQ-UTF8', 'nombre': f'Cámara {CARACTERES}',
            'categoria': 'otro', 'marca': 'Diseño Ñandú', 'modelo': 'Modelo 1',
            'numero_serie': '', 'estado': 'disponible',
            'ubicacion': 'Salón de tecnología', 'observaciones': '¿Revisión? ¡Sí!',
        }
        self.assertEqual(self.client.post(reverse('inventario:crear'), datos).status_code, 302)
        equipo = Equipo.objects.get(codigo='EQ-UTF8')
        self.assertEqual(equipo.nombre, datos['nombre'])
        datos['nombre'] = f'Cámara editada {CARACTERES}'
        self.assertEqual(self.client.post(reverse('inventario:editar', args=[equipo.pk]), datos).status_code, 302)
        equipo.refresh_from_db()
        self.assertEqual(equipo.nombre, datos['nombre'])
        lista = self.client.get(reverse('inventario:lista'), {'q': 'ñ'})
        self.assertEqual(lista.charset.lower(), 'utf-8')
        self.assertContains(lista, datos['nombre'])
        parcial = self.client.get(reverse('inventario:lista'),
                                  {'q': 'ñ', 'partial': 'tabla'}, HTTP_HX_REQUEST='true')
        self.assertEqual(parcial.charset.lower(), 'utf-8')
        self.assertContains(parcial, datos['nombre'])
        excel = self.client.get(reverse('inventario:lista'), {'q': 'ñ', 'export': 'excel'})
        libro = load_workbook(BytesIO(excel.content))
        self.assertIn(datos['nombre'], [celda for fila in libro.active.values for celda in fila])
        pdf = self.client.get(reverse('inventario:lista'), {'q': 'ñ', 'export': 'pdf'})
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b'%PDF'))

    def test_usuario_y_alerta_conservan_unicode_en_html_htmx_y_json(self):
        datos = {
            'username': 'usuario_utf8', 'email': 'utf8@example.test',
            'nombre_completo': f'Peña {CARACTERES}', 'carnet': 'UTF8-1',
            'telefono': '',
        }
        self.assertEqual(self.client.post(reverse('usuario_crear'), datos).status_code, 200)
        usuario = User.objects.get(username='usuario_utf8')
        self.assertEqual(usuario.perfil.nombre_completo, datos['nombre_completo'])
        lista = self.client.get(reverse('usuarios_lista'), {'q': 'ñ'})
        self.assertContains(lista, datos['nombre_completo'])
        parcial = self.client.get(reverse('usuarios_lista'),
                                  {'q': 'ñ', 'partial': 'tabla'}, HTTP_HX_REQUEST='true')
        self.assertContains(parcial, datos['nombre_completo'])
        datos['nombre_completo'] = f'Peña editada {CARACTERES}'
        self.assertEqual(self.client.post(reverse('usuario_editar', args=[usuario.pk]), datos).status_code, 200)
        usuario.perfil.refresh_from_db()
        self.assertEqual(usuario.perfil.nombre_completo, datos['nombre_completo'])

        titulo = f'Avería {CARACTERES}'
        Alerta.objects.create(usuario=self.admin, titulo=titulo, mensaje='Revisión mañana ¿sí?')
        respuesta = self.client.get(reverse('alertas:nueva'))
        self.assertEqual(respuesta.charset.lower(), 'utf-8')
        self.assertEqual(respuesta.json()['titulo'], titulo)
        self.assertContains(self.client.get(reverse('alertas:lista')), titulo)

    def test_fixture_corregido_y_plan_selectivo(self):
        raiz = Path(__file__).resolve().parent.parent
        fixture = json.loads((raiz / 'datos.json').read_text(encoding='utf-8'))
        plan = json.loads((raiz / 'docs' / 'REPARACIONES_UTF8_PBI_04.json').read_text(encoding='utf-8'))
        por_clave = {(obj['model'], obj['pk']): obj['fields'] for obj in fixture}
        self.assertEqual(len(plan), 51)
        for entrada in plan:
            with self.subTest(modelo=entrada['model'], pk=entrada['pk'], campo=entrada['field']):
                self.assertIn('\ufffd', entrada['expected'])
                self.assertNotIn('\ufffd', entrada['replacement'])
                self.assertEqual(por_clave[(entrada['model'], entrada['pk'])][entrada['field']],
                                 entrada['replacement'])
        self.assertNotIn('\ufffd', json.dumps(fixture, ensure_ascii=False))
