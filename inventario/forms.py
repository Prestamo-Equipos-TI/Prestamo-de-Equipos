from django import forms
from .models import Equipo


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo

        fields = [
            'codigo',
            'nombre',
            'categoria',
            'marca',
            'modelo',
            'numero_serie',
            'estado',
            'ubicacion',
            'observaciones',
        ]

        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ejemplo: EQ-001'
            }),

            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ejemplo: Laptop Dell Latitude'
            }),

            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),

            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ejemplo: Dell, HP, Epson'
            }),

            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ejemplo: Latitude 5420'
            }),

            'numero_serie': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de serie del equipo'
            }),

            'estado': forms.Select(attrs={
                'class': 'form-control'
            }),

            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ejemplo: Laboratorio IT'
            }),

            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Observaciones generales del equipo',
                'rows': 4
            }),
        }

    def clean_codigo(self):
        # Valida unicidad del código (case-insensitive), excluyendo la instancia actual en edición
        codigo = self.cleaned_data.get('codigo')

        if codigo:
            codigo = codigo.strip()

            existe = Equipo.objects.filter(codigo__iexact=codigo)

            if self.instance and self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)

            if existe.exists():
                raise forms.ValidationError(
                    'Este código ya está utilizado por otro equipo.'
                )

        return codigo

    def clean_numero_serie(self):
        # Valida unicidad del número de serie (case-insensitive), excluyendo la instancia actual en edición
        numero_serie = self.cleaned_data.get('numero_serie')

        if numero_serie:
            numero_serie = numero_serie.strip()

            existe = Equipo.objects.filter(numero_serie__iexact=numero_serie)

            if self.instance and self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)

            if existe.exists():
                raise forms.ValidationError(
                    'Este número de serie ya está utilizado por otro equipo.'
                )

        return numero_serie
