from django import forms
from datetime import date


class RegistrarDevolucionForm(forms.Form):
    fecha_devolucion_real = forms.DateField(
        label='Fecha de devolución',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    observaciones_devolucion = forms.CharField(
        label='Observaciones de devolución',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Observaciones al momento de recibir el equipo'
        })
    )

    def clean_fecha_devolucion_real(self):
        # Valida que la fecha de devolución no sea futura
        fecha = self.cleaned_data.get('fecha_devolucion_real')

        if fecha and fecha > date.today():
            raise forms.ValidationError(
                'La fecha de devolución no puede ser futura.'
            )

        return fecha
