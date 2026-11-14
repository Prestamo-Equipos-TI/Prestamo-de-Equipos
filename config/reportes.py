from datetime import date, datetime
from html import escape
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import reportlab


LOGO = settings.BASE_DIR / 'static' / 'img' / 'campbell_logo.png'
COLEGIO = 'Colegio Alexander Campbell'


def periodo_reporte(request):
    """Valida el período opcional de los reportes temporales."""
    inicio = request.GET.get('fecha_inicio', '')
    fin = request.GET.get('fecha_fin', '')
    if not inicio and not fin:
        return (None, None, 'Selecciona la fecha inicial y final.') if request.GET.get('export') else (None, None, None)
    try:
        desde, hasta = parse_date(inicio), parse_date(fin)
    except ValueError:
        desde = hasta = None
    if not desde or not hasta or desde > hasta:
        return None, None, 'Selecciona fechas válidas; la fecha inicial no puede superar la final.'
    return desde, hasta, None


def filtrar_periodo(consulta, campo, desde, hasta):
    if desde:
        sufijo = '__date' if campo in ('fecha_solicitud', 'fecha_reporte', 'fecha_creacion') else ''
        return consulta.filter(**{f'{campo}{sufijo}__range': (desde, hasta)})
    return consulta


def fecha(valor):
    if not valor:
        return '-'
    if isinstance(valor, datetime):
        if timezone.is_aware(valor):
            valor = timezone.localtime(valor)
        return valor.strftime('%d/%m/%Y %H:%M')
    if isinstance(valor, date):
        return valor.strftime('%d/%m/%Y')
    return str(valor)


def exportar_reporte(formato, nombre, titulo, secciones, *, usuario=None, desde=None, hasta=None, filtros=None):
    generado = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    autor = getattr(getattr(usuario, 'perfil', None), 'nombre_completo', None) or getattr(usuario, 'username', 'Sistema')
    total = sum(len(filas) for _, _, filas in secciones)
    filtros_texto = ', '.join(f'{clave}: {valor}' for clave, valor in (filtros or {}).items()) or 'Ninguno'
    metadatos = [
        ('Generado', generado), ('Generado por', autor),
        ('Período', f'{fecha(desde)} al {fecha(hasta)}' if desde else 'Sin período'),
        ('Filtros', filtros_texto),
        ('Total de registros', str(total)),
    ]
    if formato == 'excel':
        libro = Workbook()
        for numero, (nombre_hoja, columnas, filas) in enumerate(secciones):
            hoja = libro.active if numero == 0 else libro.create_sheet()
            hoja.title = nombre_hoja[:31]
            hoja['B1'] = COLEGIO
            hoja['B2'] = f'Control IT · {titulo} · {nombre_hoja}'
            for indice, (etiqueta, valor) in enumerate(metadatos, 3):
                hoja.cell(indice, 2, etiqueta)
                hoja.cell(indice, 3, valor)
            if LOGO.exists():
                logo = ExcelImage(str(LOGO))
                escala = min(110 / logo.width, 55 / logo.height)
                logo.width *= escala
                logo.height *= escala
                hoja.add_image(logo, 'A1')
            hoja.row_dimensions[1].height = 38
            encabezado_fila = 9
            hoja.append([])
            hoja.append(columnas)
            for celda in hoja[encabezado_fila]:
                celda.font = Font(bold=True, color='FFFFFF')
                celda.fill = PatternFill('solid', fgColor='253548')
            for fila in filas:
                hoja.append([timezone.make_naive(valor) if isinstance(valor, datetime) and timezone.is_aware(valor)
                             else valor if isinstance(valor, (date, datetime)) else str(valor) if valor is not None else ''
                             for valor in fila])
                for celda in hoja[hoja.max_row]:
                    if isinstance(celda.value, (date, datetime)):
                        celda.number_format = 'DD/MM/YYYY HH:MM' if isinstance(celda.value, datetime) else 'DD/MM/YYYY'
                    else:
                        celda.data_type = 's'  # Los textos ingresados por usuarios nunca deben convertirse en fórmulas.
            if not filas:
                hoja.append(['Sin registros para los filtros seleccionados'])
            hoja.freeze_panes = 'A10'
            hoja.auto_filter.ref = f'A9:{hoja.cell(hoja.max_row, len(columnas)).coordinate}'
            for columna in hoja.columns:
                letra = columna[0].column_letter
                hoja.column_dimensions[letra].width = min(42, max(14, *(len(str(c.value or '')) + 2 for c in columna)))
        salida = BytesIO()
        libro.save(salida)
        tipo = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        extension = 'xlsx'
    elif formato == 'pdf':
        salida = BytesIO()
        documento = SimpleDocTemplate(salida, pagesize=landscape(A4), leftMargin=1.2 * cm,
                                      rightMargin=1.2 * cm, topMargin=1.25 * cm, bottomMargin=1.3 * cm)
        fuente = Path(reportlab.__file__).parent / 'fonts' / 'Vera.ttf'
        nombre_fuente = 'Helvetica'
        fuente_negrita = 'Helvetica-Bold'
        if fuente.exists():
            if 'VeraReporte' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('VeraReporte', str(fuente)))
                pdfmetrics.registerFont(TTFont('VeraReporte-Bold', str(fuente.with_name('VeraBd.ttf'))))
                pdfmetrics.registerFontFamily('VeraReporte', normal='VeraReporte', bold='VeraReporte-Bold')
            nombre_fuente = 'VeraReporte'
            fuente_negrita = 'VeraReporte-Bold'
        navy = colors.HexColor('#253548')
        gold = colors.HexColor('#B2A21B')
        muted = colors.HexColor('#617183')
        pale = colors.HexColor('#F3F6F8')
        celda = ParagraphStyle('CeldaReporte', fontName=nombre_fuente, fontSize=7.3,
                               leading=10.5, textColor=navy)
        encabezado = ParagraphStyle('EncabezadoReporte', parent=celda, fontName=fuente_negrita,
                                    fontSize=7.2, leading=10, textColor=colors.white)
        marca = ParagraphStyle('MarcaReporte', fontName=fuente_negrita, fontSize=8,
                               leading=11, textColor=colors.HexColor('#E3D55D'))
        colegio = ParagraphStyle('ColegioReporte', fontName=fuente_negrita, fontSize=15,
                                 leading=19, textColor=colors.white)
        titulo_estilo = ParagraphStyle('TituloReporte', fontName=nombre_fuente, fontSize=10,
                                      leading=13, textColor=colors.white)
        dato = ParagraphStyle('DatoReporte', fontName=nombre_fuente, fontSize=8,
                              leading=12, textColor=navy)
        seccion_estilo = ParagraphStyle('SeccionReporte', fontName=fuente_negrita,
                                        fontSize=11, leading=15, textColor=navy)
        conteo_estilo = ParagraphStyle('ConteoReporte', fontName=nombre_fuente,
                                       fontSize=8, leading=13, alignment=2, textColor=muted)
        contenido = []
        insignia = ''
        if LOGO.exists():
            logo = Image(str(LOGO))
            escala = min(2.0 * cm / logo.imageWidth, 2.0 * cm / logo.imageHeight)
            logo.drawWidth, logo.drawHeight = logo.imageWidth * escala, logo.imageHeight * escala
            insignia = logo
        cabecera = Table([[insignia, [
            Paragraph('CONTROL IT  /  REPORTE ADMINISTRATIVO', marca),
            Paragraph(COLEGIO, colegio),
            Paragraph(escape(titulo), titulo_estilo),
        ]]], colWidths=[2.5 * cm, documento.width - 2.5 * cm])
        cabecera.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), navy),
            ('BACKGROUND', (0, 0), (0, 0), colors.white),
            ('LINEBELOW', (0, -1), (-1, -1), 2, gold),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('LEFTPADDING', (0, 0), (0, 0), 6),
            ('RIGHTPADDING', (0, 0), (0, 0), 6),
            ('LEFTPADDING', (1, 0), (1, 0), 16),
            ('TOPPADDING', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ]))
        contenido.extend([cabecera, Spacer(1, 0.35 * cm)])

        def dato_celda(etiqueta, valor):
            return Paragraph(f'<font color="#617183" size="7">{etiqueta.upper()}</font><br/>'
                             f'<b>{escape(str(valor))}</b>', dato)

        resumen = Table([[
            dato_celda('Generado', generado),
            dato_celda('Generado por', autor),
            dato_celda('Período' if desde else 'Consulta',
                       f'{fecha(desde)} al {fecha(hasta)}' if desde else 'Inventario actual'),
            dato_celda('Registros', total),
        ], [dato_celda('Filtros aplicados', filtros_texto), '', '', '']],
            colWidths=[documento.width / 4] * 4)
        resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), pale),
            ('SPAN', (0, 1), (3, 1)),
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#DCE3E8')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        contenido.extend([resumen, Spacer(1, 0.5 * cm)])
        for nombre_hoja, columnas, filas in secciones:
            barra = Table([[Paragraph(escape(nombre_hoja), seccion_estilo),
                            Paragraph(f'{len(filas)} registro' if len(filas) == 1 else
                                      f'{len(filas)} registros', conteo_estilo)]],
                          colWidths=[documento.width * 0.75, documento.width * 0.25])
            barra.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (-1, -1), 1.2, gold),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            barra.keepWithNext = True
            contenido.extend([barra, Spacer(1, 0.15 * cm)])
            datos = [[Paragraph(escape(str(valor)), encabezado) for valor in columnas]]
            datos.extend([Paragraph(escape(fecha(valor) if isinstance(valor, (date, datetime)) else
                                           str(valor if valor is not None else '')), celda)
                          for valor in fila] for fila in filas)
            if not filas:
                datos.append([Paragraph('Sin registros para los filtros seleccionados', celda)] + [''] * (len(columnas) - 1))
            tabla = LongTable(datos, colWidths=[documento.width / len(columnas)] * len(columnas), repeatRows=1)
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), navy),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LINEBELOW', (0, 1), (-1, -1), 0.35, colors.HexColor('#DCE3E8')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, pale]),
                ('LEFTPADDING', (0, 0), (-1, -1), 7),
                ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            contenido.extend([tabla, Spacer(1, 0.45 * cm)])
        def numerar(canvas, doc):
            canvas.saveState()
            ancho, alto = doc.pagesize
            if doc.page > 1:
                canvas.setStrokeColor(gold)
                canvas.setLineWidth(1)
                canvas.line(doc.leftMargin, alto - 0.72 * cm, ancho - doc.rightMargin, alto - 0.72 * cm)
                canvas.setFont(fuente_negrita, 8)
                canvas.setFillColor(navy)
                canvas.drawString(doc.leftMargin, alto - 0.58 * cm, f'{COLEGIO}  /  Control IT')
            canvas.setStrokeColor(colors.HexColor('#DCE3E8'))
            canvas.line(doc.leftMargin, 0.85 * cm, ancho - doc.rightMargin, 0.85 * cm)
            canvas.setFont(nombre_fuente, 7.5)
            canvas.setFillColor(muted)
            canvas.drawString(doc.leftMargin, 0.55 * cm, 'Control IT  |  Reporte administrativo')
            canvas.drawRightString(ancho - doc.rightMargin, 0.55 * cm, f'Página {doc.page}')
            canvas.restoreState()

        documento.build(contenido, onFirstPage=numerar, onLaterPages=numerar)
        tipo = 'application/pdf'
        extension = 'pdf'
    else:
        raise ValueError('Formato de reporte no admitido')
    respuesta = HttpResponse(salida.getvalue(), content_type=tipo)
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}.{extension}"'
    return respuesta
