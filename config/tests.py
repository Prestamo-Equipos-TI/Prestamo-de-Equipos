from io import BytesIO
from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook

from averias.models import ReporteAveria
from inventario.models import Equipo
from prestamos.models import SolicitudPrestamo
from usuarios.models import PerfilUsuario


class ReportesTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('adminqa', password='clave-segura')
        PerfilUsuario.objects.create(user=self.admin, rol='admin_ti', carnet='ADM-QA', nombre_completo='Admin QA')
        self.usuario = User.objects.create_user('usuarioqa', email='usuario@example.test', password='clave-segura')
        PerfilUsuario.objects.create(user=self.usuario, rol='usuario', carnet='USR-QA', nombre_completo='Usuario QA')
        self.equipo = Equipo.objects.create(codigo='EQ-QA-1', nombre='Laptop QA', categoria='laptop',
                                           marca='Marca QA', estado='disponible', ubicacion='Laboratorio')
        Equipo.objects.create(codigo='EQ-QA-2', nombre='Proyector QA', categoria='proyector',
                              marca='Marca QA', estado='mantenimiento', ubicacion='Bodega')
        self.solicitud = SolicitudPrestamo.objects.create(usuario=self.usuario, equipo=self.equipo,
                                                         fecha_prestamo='2026-10-27')
        ReporteAveria.objects.create(equipo=self.equipo, reportado_por=self.usuario,
                                     descripcion_falla='Pantalla con falla')
        self.client.force_login(self.admin)

    def test_inventory_export_respects_filters_and_keeps_text_safe(self):
        url = reverse('inventario:lista')
        respuesta = self.client.get(url, {'export': 'excel', 'estado': 'disponible', 'q': 'EQ-QA-1'})
        self.assertEqual(respuesta.status_code, 200)
        libro = load_workbook(BytesIO(respuesta.content))
        filas = list(libro.active.values)
        self.assertEqual(filas[8][0], 'Código')
        self.assertEqual(filas[9][0], 'EQ-QA-1')
        self.assertEqual(filas[0][1], 'Colegio Alexander Campbell')
        self.assertNotIn('EQ-QA-2', str(filas))
        self.equipo.nombre = '=1+1'
        self.equipo.save(update_fields=['nombre'])
        seguro = load_workbook(BytesIO(self.client.get(url, {'export': 'excel'}).content))
        celda = next(c for row in seguro.active.iter_rows(min_row=10) for c in row if c.value == '=1+1')
        self.assertEqual(celda.data_type, 's')
        pdf = self.client.get(url, {'export': 'pdf', 'estado': 'disponible', 'q': 'EQ-QA-1'})
        self.assertTrue(pdf.content.startswith(b'%PDF'))

    def test_every_report_downloads_and_pages_show_buttons(self):
        pages = [
            reverse('inventario:lista'),
            reverse('prestamos:solicitudes_admin'),
            reverse('historial:usuarios'),
            reverse('historial:usuario_detalle', args=[self.usuario.id]),
            reverse('historial:equipos'),
            reverse('historial:equipo_detalle', args=[self.equipo.id]),
        ]
        for url in pages:
            with self.subTest(url=url):
                page = self.client.get(url)
                es_inventario = url == reverse('inventario:lista')
                self.assertContains(page, 'Reporte PDF' if es_inventario else 'Formato de exportación')
                fechas = {} if es_inventario else {'fecha_inicio': '2000-01-01', 'fecha_fin': '2100-01-01'}
                pdf = self.client.get(url, {'export': 'pdf', **fechas})
                self.assertTrue(pdf.content.startswith(b'%PDF'))
                excel = self.client.get(url, {'export': 'excel', **fechas})
                self.assertEqual(excel.status_code, 200)
                self.assertIn('attachment;', excel['Content-Disposition'])
                self.assertGreater(len(load_workbook(BytesIO(excel.content)).sheetnames), 0)

    def test_report_content_matches_each_admin_screen(self):
        casos = [
            (reverse('prestamos:solicitudes_admin'), 'Solicitudes', 'Usuario QA'),
            (reverse('historial:usuarios'), 'Solicitudes', 'EQ-QA-1'),
            (reverse('historial:usuario_detalle', args=[self.usuario.id]), 'Solicitudes', 'EQ-QA-1'),
            (reverse('historial:equipos'), 'Averías', 'Pantalla con falla'),
            (reverse('historial:equipo_detalle', args=[self.equipo.id]), 'Averías', 'Pantalla con falla'),
        ]
        for url, hoja, valor in casos:
            with self.subTest(url=url):
                respuesta = self.client.get(url, {'export': 'excel', 'fecha_inicio': '2000-01-01',
                                                  'fecha_fin': '2100-01-01'})
                libro = load_workbook(BytesIO(respuesta.content))
                self.assertIn(hoja, libro.sheetnames)
                self.assertIn(valor, [celda for fila in libro[hoja].values for celda in fila])

    def test_report_pages_are_admin_only(self):
        self.client.force_login(self.usuario)
        self.assertNotContains(self.client.get(reverse('prestamos:solicitar')), 'Reporte PDF')
        self.assertNotContains(self.client.get(reverse('prestamos:mis_solicitudes')), 'Reporte Excel')
        for url in (reverse('inventario:lista'), reverse('prestamos:solicitudes_admin'),
                    reverse('historial:usuarios'), reverse('historial:equipos')):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.get(url, {'export': 'excel'}).status_code, 403)

    def test_reports_require_login(self):
        self.client.logout()
        for url in (reverse('inventario:lista'), reverse('historial:equipos')):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url, {'export': 'pdf'}).status_code, 302)

    def test_period_boundaries_validation_and_empty_exports(self):
        SolicitudPrestamo.objects.filter(pk=self.solicitud.pk).update(
            fecha_solicitud=timezone.make_aware(datetime(2026, 10, 31, 12)))
        url = reverse('prestamos:solicitudes_admin')
        self.assertEqual(self.client.get(url, {'export': 'pdf'}).status_code, 400)
        for formato in ('pdf', 'excel'):
            with self.subTest(formato=formato):
                consulta = {'export': formato, 'fecha_inicio': '2026-10-01', 'fecha_fin': '2026-10-31'}
                respuesta = self.client.get(url, consulta)
                self.assertEqual(respuesta.status_code, 200)
                if formato == 'excel':
                    libro = load_workbook(BytesIO(respuesta.content))
                    self.assertIn('Usuario QA', [c for row in libro.active.values for c in row])
                    self.assertEqual(libro.active['C5'].value, '01/10/2026 al 31/10/2026')
                    self.assertIsInstance(libro.active['G10'].value, datetime)
                else:
                    self.assertTrue(respuesta.content.startswith(b'%PDF'))
                consulta['fecha_inicio'] = '2026-11-01'
                consulta['fecha_fin'] = '2026-11-30'
                vacio = self.client.get(url, consulta)
                self.assertEqual(vacio.status_code, 200)
                if formato == 'excel':
                    self.assertIn('Sin registros', str(list(load_workbook(BytesIO(vacio.content)).active.values)))
                consulta['fecha_inicio'] = '2026-12-01'
                self.assertEqual(self.client.get(url, consulta).status_code, 400)
                consulta['fecha_inicio'] = 'fecha-rota'
                self.assertEqual(self.client.get(url, consulta).status_code, 400)
                consulta['fecha_inicio'] = '2026-02-31'
                self.assertEqual(self.client.get(url, consulta).status_code, 400)

    def test_history_sections_use_their_own_dates(self):
        SolicitudPrestamo.objects.filter(pk=self.solicitud.pk).update(
            fecha_solicitud=timezone.make_aware(datetime(2026, 10, 1, 12)))
        ReporteAveria.objects.update(fecha_reporte=timezone.make_aware(datetime(2026, 10, 31, 12)))
        consulta = {'export': 'excel', 'fecha_inicio': '2026-10-31', 'fecha_fin': '2026-10-31'}
        for url in (reverse('historial:equipos'), reverse('historial:equipo_detalle', args=[self.equipo.id])):
            with self.subTest(url=url):
                libro = load_workbook(BytesIO(self.client.get(url, consulta).content))
                self.assertNotIn('Usuario QA', [c for row in libro['Préstamos'].values for c in row])
                self.assertIn('Pantalla con falla', [c for row in libro['Averías'].values for c in row])

    def test_inventory_new_filters_affect_export(self):
        respuesta = self.client.get(reverse('inventario:lista'),
                                   {'export': 'excel', 'nombre': 'Laptop', 'marca': 'Marca QA',
                                    'modelo': 'nada'})
        hoja = load_workbook(BytesIO(respuesta.content)).active
        self.assertEqual(hoja['C6'].value, 'Modelo: nada, Nombre: Laptop, Marca: Marca QA')
        self.assertIn('Sin registros', hoja['A10'].value)
