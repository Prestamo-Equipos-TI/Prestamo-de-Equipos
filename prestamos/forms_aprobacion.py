from django import forms
from datetime import date


class AprobarSolicitudForm(forms.Form):
    fecha_entrega_programada = forms.DateField(
        label='Fecha de entrega programada',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    dias_prestamo = forms.IntegerField(
        label='Días de préstamo',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ejemplo: 3'
        })
    )

    def clean_fecha_entrega_programada(self):
        fecha = self.cleaned_data.get('fecha_entrega_programada')

        if fecha and fecha < date.today():
            raise forms.ValidationError(
                'La fecha de entrega no puede ser pasada.'
            )

        return fecha