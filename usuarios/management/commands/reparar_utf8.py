import json
import os
from datetime import datetime, timezone
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


CAMPOS_PERMITIDOS = {
    'alertas.alerta': {'titulo', 'mensaje'},
    'averias.reporteaveria': {'descripcion_falla'},
}


def cargar_entradas(ruta, respaldo=False):
    try:
        contenido = json.loads(Path(ruta).read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CommandError(f'No se pudo leer el plan: {exc}') from exc
    if respaldo:
        if not isinstance(contenido, dict) or contenido.get('version') != 1 or contenido.get('accion') != 'reparacion':
            raise CommandError('El archivo no es un respaldo de reparación válido.')
        if contenido.get('base') != str(connection.settings_dict['NAME']):
            raise CommandError('El respaldo pertenece a otra base de datos.')
    entradas = contenido.get('entries') if respaldo else contenido
    if not isinstance(entradas, list) or not entradas:
        raise CommandError('El plan debe contener una lista no vacía de correcciones.')
    vistas = set()
    for entrada in entradas:
        if not isinstance(entrada, dict) or set(entrada) != {
            'model', 'pk', 'field', 'expected', 'replacement'
        }:
            raise CommandError('Una entrada del plan tiene un formato no válido.')
        modelo = entrada['model']
        campo = entrada['field']
        if modelo not in CAMPOS_PERMITIDOS or campo not in CAMPOS_PERMITIDOS[modelo]:
            raise CommandError(f'Campo no autorizado: {modelo}.{campo}.')
        if type(entrada['pk']) is not int or entrada['pk'] < 1:
            raise CommandError('Cada ID debe ser un entero positivo.')
        anterior = entrada['expected']
        nuevo = entrada['replacement']
        if not isinstance(anterior, str) or not isinstance(nuevo, str):
            raise CommandError('Los valores deben ser texto.')
        if '\ufffd' not in anterior or '\ufffd' in nuevo or anterior == nuevo:
            raise CommandError('Solo se admiten correcciones explícitas de texto con U+FFFD.')
        modelo_django = apps.get_model(modelo)
        longitud = modelo_django._meta.get_field(campo).max_length
        if longitud and len(nuevo) > longitud:
            raise CommandError(f'Valor demasiado largo para {modelo}.{campo}.')
        clave = (modelo, entrada['pk'], campo)
        if clave in vistas:
            raise CommandError(f'Entrada duplicada: {clave}.')
        vistas.add(clave)
    return entradas


def ruta_segura(nombre):
    ruta = Path(nombre)
    if not ruta.is_absolute() or ruta.resolve().is_relative_to(Path(settings.BASE_DIR).resolve()):
        raise CommandError('El respaldo debe usar una ruta absoluta fuera del repositorio.')
    if not ruta.parent.is_dir():
        raise CommandError('La carpeta del respaldo no existe.')
    if ruta.exists():
        raise CommandError('El archivo de respaldo ya existe; no se sobrescribirá.')
    return ruta


def guardar_registro(ruta, entradas, accion):
    datos = {
        'version': 1,
        'accion': accion,
        'fecha_utc': datetime.now(timezone.utc).isoformat(),
        'base': str(connection.settings_dict['NAME']),
        'entries': entradas,
    }
    descriptor = os.open(ruta, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
        archivo.write('\n')


class Command(BaseCommand):
    help = 'Simula, aplica o revierte correcciones UTF-8 exactas con respaldo obligatorio.'

    def add_arguments(self, parser):
        grupo = parser.add_mutually_exclusive_group(required=True)
        grupo.add_argument('--plan')
        grupo.add_argument('--revertir')
        parser.add_argument('--aplicar', action='store_true')
        parser.add_argument('--respaldo')
        parser.add_argument('--registro-reversion')

    def handle(self, *args, **opciones):
        reverso = bool(opciones['revertir'])
        entradas = cargar_entradas(opciones['revertir'] or opciones['plan'], respaldo=reverso)
        if opciones['aplicar']:
            destino = opciones['registro_reversion'] if reverso else opciones['respaldo']
            if not destino:
                raise CommandError('Para aplicar se requiere respaldo o registro de reversión.')
            ruta = ruta_segura(destino)
        else:
            ruta = None

        with transaction.atomic():
            conflictos = []
            for entrada in entradas:
                modelo = apps.get_model(entrada['model'])
                consulta = modelo.objects.filter(pk=entrada['pk'])
                if opciones['aplicar']:
                    consulta = consulta.select_for_update()
                actual = consulta.values_list(entrada['field'], flat=True).first()
                esperado = entrada['replacement'] if reverso else entrada['expected']
                if actual != esperado:
                    conflictos.append(f"{entrada['model']} ID {entrada['pk']} campo {entrada['field']}")
            if conflictos:
                raise CommandError(
                    f'{len(conflictos)} valores distintos al plan; no se cambió nada: '
                    + ', '.join(conflictos[:5])
                )
            accion = 'reversion' if reverso else 'reparacion'
            if ruta:
                guardar_registro(ruta, entradas, accion)
                for entrada in entradas:
                    modelo = apps.get_model(entrada['model'])
                    valor = entrada['expected'] if reverso else entrada['replacement']
                    modelo.objects.filter(pk=entrada['pk']).update(**{entrada['field']: valor})
        estado = 'Aplicadas' if ruta else 'Simuladas'
        self.stdout.write(self.style.SUCCESS(
            f'{estado} {len(entradas)} correcciones ({accion}).'
        ))
        if ruta:
            self.stdout.write(f'Registro: {ruta}')
