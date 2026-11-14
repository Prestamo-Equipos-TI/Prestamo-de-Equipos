from datetime import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usuarios.models import PerfilUsuario
from .models import Alerta


class ReporteAlertasTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin_alertas', password='clave-segura')
        PerfilUsuario.objects.create(user=self.admin, rol=PerfilUsuario.ROL_ADMIN_TI,
                                    carnet='ADM-A', nombre_completo='Admin Alertas')
        self.usuario = User.objects.create_user('usuario_alertas', password='clave-segura')
        PerfilUsuario.objects.create(user=self.usuario, rol=PerfilUsuario.ROL_USUARIO,
                                    carnet='USR-A', nombre_completo='Usuario Alertas')
        self.inicio = Alerta.objects.create(usuario=self.admin, titulo='Inicio octubre',
                                           mensaje='Solicitud aprobada', tipo=Alerta.TIPO_PRESTAMO_APROBADO)
        self.fin = Alerta.objects.create(usuario=self.admin, titulo='Fin octubre',
                                        mensaje='Entrega realizada', tipo=Alerta.TIPO_PRESTAMO_ENTREGADO)
        self.fuera = Alerta.objects.create(usuario=self.admin, titulo='Noviembre',
                                          mensaje='Fuera del período', tipo=Alerta.TIPO_PRESTAMO_ENTREGADO)
        Alerta.objects.create(usuario=self.usuario, titulo='Alerta privada', mensaje='Solo del usuario')
        for alerta, dia in ((self.inicio, 1), (self.fin, 31), (self.fuera, 1)):
            mes = 11 if alerta == self.fuera else 10
            Alerta.objects.filter(pk=alerta.pk).update(
                fecha_creacion=timezone.make_aware(datetime(2026, mes, dia, 12)))
        self.url = reverse('alertas:lista')
        self.client.force_login(self.admin)

    def test_pdf_usa_periodo_inclusivo_tipo_y_usuario_actual(self):
        parametros = {'export': 'pdf', 'fecha_inicio': '2026-10-01',
                      'fecha_fin': '2026-10-31', 'tipo': Alerta.TIPO_PRESTAMO_ENTREGADO}
        with patch('alertas.views.exportar_reporte', return_value=HttpResponse(b'%PDF')) as exportar:
            respuesta = self.client.get(self.url, parametros)
        self.assertEqual(respuesta.status_code, 200)
        args, kwargs = exportar.call_args
        filas = args[3][0][2]
        self.assertEqual([fila[0] for fila in filas], ['Fin octubre'])
        self.assertEqual(kwargs['usuario'], self.admin)
        self.assertEqual(kwargs['filtros'], {'Tipo de alerta': 'Préstamo entregado'})
        self.fin.refresh_from_db()
        self.assertFalse(self.fin.leida)

        pdf = self.client.get(self.url, parametros)
        self.assertTrue(pdf.content.startswith(b'%PDF'))

    def test_pantalla_filtra_por_tipo_y_fechas(self):
        respuesta = self.client.get(self.url, {'fecha_inicio': '2026-10-31',
                                               'fecha_fin': '2026-10-31',
                                               'tipo': Alerta.TIPO_PRESTAMO_ENTREGADO})
        self.assertContains(respuesta, 'Fin octubre')
        self.assertNotContains(respuesta, 'Inicio octubre')
        self.assertNotContains(respuesta, 'Noviembre')
        self.assertNotContains(respuesta, 'Alerta privada')
        self.assertContains(respuesta, 'Generar PDF')
        solo_tipo = self.client.get(self.url, {'tipo': Alerta.TIPO_PRESTAMO_APROBADO})
        self.assertContains(solo_tipo, 'Inicio octubre')
        self.assertNotContains(solo_tipo, 'Fin octubre')
        parcial = self.client.get(self.url, {'tipo': Alerta.TIPO_PRESTAMO_APROBADO},
                                  HTTP_HX_REQUEST='true')
        self.assertContains(parcial, 'Inicio octubre')
        self.assertNotContains(parcial, '<!DOCTYPE html>')
        self.assertContains(parcial, 'hx-target="#alert-results"')
        self.assertContains(parcial, 'id="alert-results"')

    def test_filtros_invalidos_y_periodo_vacio(self):
        for parametros in (
            {'export': 'pdf'},
            {'export': 'pdf', 'fecha_inicio': '2026-11-01', 'fecha_fin': '2026-10-31'},
            {'export': 'pdf', 'fecha_inicio': '2026-02-31', 'fecha_fin': '2026-10-31'},
            {'export': 'pdf', 'fecha_inicio': '2026-10-01', 'fecha_fin': '2026-10-31', 'tipo': 'otro'},
        ):
            with self.subTest(parametros=parametros):
                self.assertEqual(self.client.get(self.url, parametros).status_code, 400)
        vacio = self.client.get(self.url, {'export': 'pdf', 'fecha_inicio': '2026-09-01',
                                           'fecha_fin': '2026-09-30'})
        self.assertEqual(vacio.status_code, 200)
        self.assertTrue(vacio.content.startswith(b'%PDF'))

    def test_pdf_reservado_a_gestores_ti(self):
        self.client.force_login(self.usuario)
        pagina = self.client.get(self.url)
        self.assertEqual(pagina.status_code, 200)
        self.assertNotContains(pagina, 'Generar PDF')
        respuesta = self.client.get(self.url, {'export': 'pdf', 'fecha_inicio': '2026-10-01',
                                               'fecha_fin': '2026-10-31'})
        self.assertEqual(respuesta.status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(self.url, {'export': 'pdf'}).status_code, 302)

        superadmin = User.objects.create_user('super_alertas', password='clave-segura')
        PerfilUsuario.objects.create(user=superadmin, rol=PerfilUsuario.ROL_SUPERADMIN,
                                    carnet='SUP-A', nombre_completo='Superadmin Alertas')
        self.client.force_login(superadmin)
        self.assertContains(self.client.get(self.url), 'Generar PDF')
        pdf = self.client.get(self.url, {'export': 'pdf', 'fecha_inicio': '2026-10-01',
                                         'fecha_fin': '2026-10-31'})
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b'%PDF'))
