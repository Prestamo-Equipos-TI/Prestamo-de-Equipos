from django import forms
from .models import SolicitudPrestamo


class SolicitudPrestamoForm(forms.ModelForm):
    class Meta:
        model = SolicitudPrestamo

        fields = [
            'fecha_prestamo',
            'observaciones',
        ]

        widgets = {
            'fecha_prestamo': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),

            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observaciones opcionales'
            }),
        }

    def clean_fecha_prestamo(self):
        # Valida que la fecha de préstamo no sea anterior a hoy
        fecha = self.cleaned_data.get('fecha_prestamo')

        if fecha:
            from datetime import date

            if fecha < date.today():
                raise forms.ValidationError(
                    'No puedes solicitar una fecha pasada.'
                )

        return fecha
