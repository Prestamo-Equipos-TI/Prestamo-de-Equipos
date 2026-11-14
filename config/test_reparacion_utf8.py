import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from alertas.models import Alerta
from averias.models import ReporteAveria
from inventario.models import Equipo


class ReparacionUtf8Test(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('operador')
        self.equipo = Equipo.objects.create(
            codigo='EQ-U1', nombre='Cámara', categoria='otro', marca='Marca',
            ubicacion='Aula',
        )
        self.alerta = Alerta.objects.create(
            usuario=self.usuario, titulo='Pr\ufffdstamo aprobado', mensaje='D\ufffda de entrega',
        )
        self.sana = Alerta.objects.create(
            usuario=self.usuario, titulo='Préstamo aprobado', mensaje='Día de entrega',
        )
        self.averia = ReporteAveria.objects.create(
            equipo=self.equipo, descripcion_falla='Pantalla da\ufffdada',
        )

    def plan(self):
        return [
            {'model': 'alertas.alerta', 'pk': self.alerta.pk, 'field': 'titulo',
             'expected': 'Pr\ufffdstamo aprobado', 'replacement': 'Préstamo aprobado'},
            {'model': 'alertas.alerta', 'pk': self.alerta.pk, 'field': 'mensaje',
             'expected': 'D\ufffda de entrega', 'replacement': 'Día de entrega'},
            {'model': 'averias.reporteaveria', 'pk': self.averia.pk,
             'field': 'descripcion_falla', 'expected': 'Pantalla da\ufffdada',
             'replacement': 'Pantalla dañada'},
        ]

    def test_simulacion_respaldo_aplicacion_y_reversion(self):
        with TemporaryDirectory() as carpeta:
            plan = Path(carpeta) / 'plan.json'
            respaldo = Path(carpeta) / 'respaldo.json'
            registro = Path(carpeta) / 'reversion.json'
            plan.write_text(json.dumps(self.plan(), ensure_ascii=False), encoding='utf-8')
            call_command('reparar_utf8', plan=str(plan), verbosity=0)
            self.alerta.refresh_from_db()
            self.assertEqual(self.alerta.titulo, 'Pr\ufffdstamo aprobado')
            self.assertFalse(respaldo.exists())
            call_command('reparar_utf8', plan=str(plan), aplicar=True,
                         respaldo=str(respaldo), verbosity=0)
            self.alerta.refresh_from_db()
            self.averia.refresh_from_db()
            self.sana.refresh_from_db()
            self.assertEqual((self.alerta.titulo, self.alerta.mensaje),
                             ('Préstamo aprobado', 'Día de entrega'))
            self.assertEqual(self.averia.descripcion_falla, 'Pantalla dañada')
            self.assertEqual(self.sana.titulo, 'Préstamo aprobado')
            self.assertEqual(len(json.loads(respaldo.read_text(encoding='utf-8'))['entries']), 3)
            call_command('reparar_utf8', revertir=str(respaldo), verbosity=0)
            call_command('reparar_utf8', revertir=str(respaldo), aplicar=True,
                         registro_reversion=str(registro), verbosity=0)
            self.alerta.refresh_from_db()
            self.assertEqual(self.alerta.titulo, 'Pr\ufffdstamo aprobado')
            self.assertTrue(registro.exists())

    def test_conflicto_cancela_todo_sin_respaldo(self):
        with TemporaryDirectory() as carpeta:
            plan = Path(carpeta) / 'plan.json'
            respaldo = Path(carpeta) / 'respaldo.json'
            entradas = self.plan()
            entradas[1]['expected'] = 'otro texto \ufffd'
            plan.write_text(json.dumps(entradas, ensure_ascii=False), encoding='utf-8')
            with self.assertRaises(CommandError):
                call_command('reparar_utf8', plan=str(plan), aplicar=True,
                             respaldo=str(respaldo), verbosity=0)
            self.assertFalse(respaldo.exists())
            self.alerta.refresh_from_db()
            self.assertEqual(self.alerta.titulo, 'Pr\ufffdstamo aprobado')

    def test_rechaza_campo_sensible_y_texto_sano(self):
        with TemporaryDirectory() as carpeta:
            plan = Path(carpeta) / 'plan.json'
            for entrada in (
                {'model': 'auth.user', 'pk': self.usuario.pk, 'field': 'password',
                 'expected': 'clave \ufffd', 'replacement': 'clave nueva'},
                {'model': 'alertas.alerta', 'pk': self.sana.pk, 'field': 'titulo',
                 'expected': 'Préstamo aprobado', 'replacement': 'Otro texto'},
            ):
                plan.write_text(json.dumps([entrada], ensure_ascii=False), encoding='utf-8')
                with self.assertRaises(CommandError):
                    call_command('reparar_utf8', plan=str(plan), verbosity=0)
