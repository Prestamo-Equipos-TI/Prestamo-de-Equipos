from django import forms
from datetime import date


class RegistrarEntregaForm(forms.Form):
    fecha_entrega_real = forms.DateField(
        label='Fecha real de entrega',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    observaciones_entrega = forms.CharField(
        label='Observaciones de entrega',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Observaciones al momento de entregar el equipo'
        })
    )

    def clean_fecha_entrega_real(self):
        fecha = self.cleaned_data.get('fecha_entrega_real')

        if fecha and fecha < date.today():
            raise forms.ValidationError(
                'La fecha de entrega no puede ser pasada.'
            )

        return fecha