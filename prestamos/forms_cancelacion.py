from django import forms


class CancelarSolicitudForm(forms.Form):
    motivo = forms.CharField(
        label='Motivo de cancelación', min_length=3, max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 4,
            'placeholder': 'Explica por qué se cancela la solicitud',
        }),
    )

    def clean_motivo(self):
        motivo = self.cleaned_data['motivo'].strip()
        if len(motivo) < 3:
            raise forms.ValidationError('Indica un motivo de al menos 3 caracteres.')
        return motivo
