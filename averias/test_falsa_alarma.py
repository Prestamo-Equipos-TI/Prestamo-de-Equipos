from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from alertas.models import Alerta
from inventario.models import Equipo
from prestamos.models import SolicitudPrestamo
from usuarios.models import PerfilUsuario

from .models import RegistroCierreAveria, ReporteAveria


class FalsaAlarmaTests(TestCase):
    def setUp(self):
        self.usuario = self.crear_usuario('usuario', 'usuario')
        self.admin = self.crear_usuario('admin', 'admin_ti')
        self.superadmin = self.crear_usuario('superadmin', 'superadmin')
        self.equipo = Equipo.objects.create(
            codigo='PBI07', nombre='Equipo PBI-07', categoria='laptop',
            marca='Marca', ubicacion='Bodega', estado='averiado',
        )
        self.reporte = ReporteAveria.objects.create(
            equipo=self.equipo, reportado_por=self.usuario,
            descripcion_falla='No enciende',
        )

    def crear_usuario(self, nombre, rol):
        usuario = User.objects.create_user(username=nombre, password='prueba-segura')
        PerfilUsuario.objects.create(
            user=usuario, rol=rol, carnet=nombre, nombre_completo=nombre,
        )
        return usuario

    def cerrar(self, actor, motivo='Fue un error de conexión'):
        self.client.force_login(actor)
        return self.client.post(
            reverse('averias:confirmar_falsa_alarma', args=[self.reporte.pk]),
            {'motivo': motivo}, HTTP_HX_REQUEST='true',
        )

    def test_permisos_motivo_auditoria_y_doble_cierre(self):
        self.assertEqual(self.cerrar(self.usuario).status_code, 403)
        self.assertEqual(self.cerrar(self.admin, '  ').status_code, 422)
        self.assertEqual(self.cerrar(self.admin).status_code, 204)
        self.reporte.refresh_from_db()
        self.equipo.refresh_from_db()
        self.assertEqual(self.reporte.estado, 'falsa_alarma')
        self.assertIsNotNone(self.reporte.fecha_resolucion)
        self.assertEqual(self.equipo.estado, 'disponible')
        registro = RegistroCierreAveria.objects.get(reporte=self.reporte)
        self.assertEqual((registro.actor, registro.estado_anterior,
                          registro.estado_nuevo, registro.motivo),
                         (self.admin, 'pendiente', 'falsa_alarma',
                          'Fue un error de conexión'))
        self.assertTrue(Alerta.objects.filter(usuario=self.usuario).exists())
        self.assertEqual(self.cerrar(self.admin).status_code, 404)
        self.assertEqual(self.reporte.cierres.count(), 1)

    def test_superadmin_y_reporte_en_revision(self):
        self.reporte.estado = 'en_revision'
        self.reporte.save(update_fields=['estado'])
        self.assertEqual(self.cerrar(self.superadmin).status_code, 204)
        self.assertEqual(self.reporte.cierres.get().estado_anterior, 'en_revision')

    def test_reporte_resuelto_no_se_reabre(self):
        self.reporte.estado = 'resuelta'
        self.reporte.save(update_fields=['estado'])
        self.assertEqual(self.cerrar(self.admin).status_code, 404)

    def test_prestamo_entregado_impide_liberacion(self):
        SolicitudPrestamo.objects.create(
            usuario=self.usuario, equipo=self.equipo,
            fecha_prestamo=date.today(), estado='entregado',
        )
        self.assertEqual(self.cerrar(self.admin).status_code, 204)
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'prestado')

    def test_reserva_impide_liberacion(self):
        SolicitudPrestamo.objects.create(
            usuario=self.usuario, equipo=self.equipo,
            fecha_prestamo=date.today(), estado='aprobado',
        )
        self.assertEqual(self.cerrar(self.admin).status_code, 204)
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'reservado')

    def test_mantenimiento_impide_liberacion(self):
        self.equipo.estado = 'mantenimiento'
        self.equipo.save(update_fields=['estado'])
        self.assertEqual(self.cerrar(self.admin).status_code, 204)
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'mantenimiento')

    def test_otra_averia_activa_impide_liberacion(self):
        ReporteAveria.objects.create(
            equipo=self.equipo, descripcion_falla='Otra falla',
        )
        self.assertEqual(self.cerrar(self.admin).status_code, 204)
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'averiado')

    def test_equipo_inactivo_impide_liberacion(self):
        self.equipo.activo = False
        self.equipo.save(update_fields=['activo'])
        self.assertEqual(self.cerrar(self.admin).status_code, 204)
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'mantenimiento')

    def test_historial_solo_gestion_ti(self):
        self.cerrar(self.admin)
        url = reverse('averias:historial_cierre', args=[self.reporte.pk])
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(url), 'Fue un error de conexión')

    def test_accion_y_formulario_visibles_para_ti(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('averias:admin_lista')), 'Falsa alarma')
        self.assertContains(self.client.get(
            reverse('averias:falsa_alarma_modal', args=[self.reporte.pk]),
            HTTP_HX_REQUEST='true',
        ), 'Motivo del cierre')
