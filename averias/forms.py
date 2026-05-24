from django import forms


class ReporteAveriaForm(forms.Form):
    descripcion_falla = forms.CharField(
        label='Descripción de la falla',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Describe detalladamente la falla detectada'
        })
    )


class GestionarAveriaForm(forms.Form):
    ACCION_SIN_CAMBIO = 'sin_cambio'
    ACCION_MANTENIMIENTO = 'mantenimiento'
    ACCION_AVERIADO = 'averiado'
    ACCION_VISITA_EXTERNA = 'visita_externa'

    ACCIONES = [
        (ACCION_SIN_CAMBIO, 'Diagnóstico sin cambio de estado'),
        (ACCION_MANTENIMIENTO, 'Enviar a mantenimiento'),
        (ACCION_AVERIADO, 'Marcar como averiado'),
        (ACCION_VISITA_EXTERNA, 'Coordinar visita técnica externa'),
    ]

    accion_tomada = forms.ChoiceField(
        label='Acción tomada',
        choices=ACCIONES,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    observaciones_revision = forms.CharField(
        label='Observaciones de revisión',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Detalle de la revisión realizada'
        })
    )


class ResolverAveriaForm(forms.Form):
    ESTADO_SIN_CAMBIO = 'sin_cambio'
    ESTADO_DISPONIBLE = 'disponible'
    ESTADO_MANTENIMIENTO = 'mantenimiento'
    ESTADO_AVERIADO = 'averiado'

    ESTADOS_FINALES_EQUIPO = [
        (ESTADO_SIN_CAMBIO, 'No cambiar estado del equipo'),
        (ESTADO_DISPONIBLE, 'Marcar como disponible'),
        (ESTADO_MANTENIMIENTO, 'Mantener en mantenimiento'),
        (ESTADO_AVERIADO, 'Mantener como averiado'),
    ]

    estado_final_equipo = forms.ChoiceField(
        label='Estado final del equipo',
        choices=ESTADOS_FINALES_EQUIPO,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    observaciones_resolucion = forms.CharField(
        label='Observaciones de resolución',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe cómo se resolvió la avería'
        })
    )