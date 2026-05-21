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