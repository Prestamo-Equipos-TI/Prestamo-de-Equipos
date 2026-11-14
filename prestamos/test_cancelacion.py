from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from alertas.models import Alerta
from averias.models import ReporteAveria
from inventario.models import Equipo
from usuarios.models import PerfilUsuario

from .models import RegistroEstadoSolicitud, SolicitudPrestamo


class CancelacionTests(TestCase):
    def setUp(self):
        self.dueno = self.usuario('dueno', PerfilUsuario.ROL_USUARIO)
        self.otro = self.usuario('otro', PerfilUsuario.ROL_USUARIO)
        self.admin = self.usuario('admin', PerfilUsuario.ROL_ADMIN_TI)
        self.equipo = Equipo.objects.create(
            codigo='PBI06', nombre='Laptop de prueba', categoria='laptop',
            marca='Marca', ubicacion='Bodega',
        )
        self.solicitud = SolicitudPrestamo.objects.create(
            usuario=self.dueno, equipo=self.equipo, fecha_prestamo=date.today(),
        )

    def usuario(self, nombre, rol):
        user = User.objects.create_user(username=nombre, password='prueba-segura')
        PerfilUsuario.objects.create(
            user=user, rol=rol, carnet=nombre, nombre_completo=nombre,
        )
        return user

    def cancelar(self, actor, motivo='Motivo válido'):
        self.client.force_login(actor)
        return self.client.post(
            reverse('prestamos:cancelar_solicitud', args=[self.solicitud.pk]),
            {'motivo': motivo}, HTTP_HX_REQUEST='true',
        )

    def test_pendiente_solo_propietario_o_ti_con_motivo(self):
        self.assertEqual(self.cancelar(self.otro).status_code, 404)
        self.assertEqual(self.cancelar(self.dueno, '  ').status_code, 422)
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'pendiente')
        self.assertEqual(self.cancelar(self.dueno).status_code, 204)
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'cancelado')
        self.assertEqual(self.equipo.estado, 'disponible')
        registro = RegistroEstadoSolicitud.objects.get(solicitud=self.solicitud)
        self.assertEqual((registro.actor, registro.estado_anterior, registro.estado_nuevo),
                         (self.dueno, 'pendiente', 'cancelado'))
        self.assertTrue(Alerta.objects.filter(usuario=self.admin).exists())
        self.assertEqual(self.cancelar(self.dueno).status_code, 404)

    def test_aprobada_solo_ti_libera_reserva(self):
        self.solicitud.estado = 'aprobado'
        self.solicitud.save(update_fields=['estado'])
        self.equipo.estado = 'reservado'
        self.equipo.save(update_fields=['estado'])
        self.assertEqual(self.cancelar(self.dueno).status_code, 404)
        self.assertEqual(self.cancelar(self.admin).status_code, 204)
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'disponible')
        self.assertTrue(Alerta.objects.filter(usuario=self.dueno).exists())

    def test_admin_puede_cancelar_pendiente(self):
        self.assertEqual(self.cancelar(self.admin).status_code, 204)
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'cancelado')

    def test_otra_reserva_impide_liberar_equipo(self):
        self.solicitud.estado = 'aprobado'
        self.solicitud.save(update_fields=['estado'])
        SolicitudPrestamo.objects.create(
            usuario=self.otro, equipo=self.equipo, fecha_prestamo=date.today(),
            estado='aprobado',
        )
        self.equipo.estado = 'reservado'
        self.equipo.save(update_fields=['estado'])
        self.assertEqual(self.cancelar(self.admin).status_code, 204)
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'reservado')

    def test_entregada_requiere_retorno_fisico(self):
        self.solicitud.estado = 'entregado'
        self.solicitud.fecha_entrega_real = date.today()
        self.solicitud.fecha_devolucion_estimada = date.today() + timedelta(days=3)
        self.solicitud.save()
        self.equipo.estado = 'prestado'
        self.equipo.save(update_fields=['estado'])
        self.assertEqual(self.cancelar(self.dueno).status_code, 404)
        self.assertEqual(self.cancelar(self.admin).status_code, 204)
        self.solicitud.refresh_from_db()
        self.equipo.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'cancelacion_pendiente')
        self.assertIsNone(self.solicitud.fecha_devolucion_real)
        self.assertEqual(self.equipo.estado, 'prestado')
        self.assertEqual(self.cancelar(self.admin).status_code, 404)
        self.assertContains(self.client.get(reverse('prestamos:devoluciones')), 'Laptop de prueba')
        self.assertEqual(self.client.post(
            reverse('prestamos:confirmar_devolucion', args=[self.solicitud.pk]),
            {'condicion': 'operativo', 'fecha_devolucion_real': date.today().isoformat()},
            HTTP_HX_REQUEST='true',
        ).status_code, 204)
        self.solicitud.refresh_from_db()
        self.equipo.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'cancelado')
        self.assertEqual(self.solicitud.fecha_devolucion_real, date.today())
        self.assertEqual(self.equipo.estado, 'disponible')
        self.assertEqual(self.solicitud.transiciones.count(), 2)
        self.assertEqual(self.client.post(
            reverse('prestamos:confirmar_devolucion', args=[self.solicitud.pk]),
            {'condicion': 'operativo', 'fecha_devolucion_real': date.today().isoformat()},
        ).status_code, 404)

    def test_retorno_con_mantenimiento_no_libera(self):
        self.solicitud.estado = 'cancelacion_pendiente'
        self.solicitud.save(update_fields=['estado'])
        self.equipo.estado = 'prestado'
        self.equipo.save(update_fields=['estado'])
        self.client.force_login(self.admin)
        self.client.post(reverse('prestamos:confirmar_devolucion', args=[self.solicitud.pk]), {
            'condicion': 'mantenimiento', 'fecha_devolucion_real': date.today().isoformat(),
        })
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'mantenimiento')

    def test_averia_activa_impide_disponibilidad(self):
        self.solicitud.estado = 'aprobado'
        self.solicitud.save(update_fields=['estado'])
        self.equipo.estado = 'reservado'
        self.equipo.save(update_fields=['estado'])
        ReporteAveria.objects.create(
            equipo=self.equipo, reportado_por=self.dueno, descripcion_falla='Falla',
        )
        self.assertEqual(self.cancelar(self.admin).status_code, 204)
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.estado, 'averiado')

    def test_historial_ajeno_oculto(self):
        self.cancelar(self.admin)
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(
            reverse('prestamos:historial_cancelacion', args=[self.solicitud.pk]),
        ).status_code, 404)
        self.client.force_login(self.dueno)
        self.assertContains(self.client.get(
            reverse('prestamos:historial_cancelacion', args=[self.solicitud.pk]),
        ), 'Motivo válido')
