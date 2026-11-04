from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator

from .models import PerfilUsuario


class SolicitanteForm(forms.Form):
    username = forms.CharField(
        label='Usuario', max_length=150, validators=[UnicodeUsernameValidator()]
    )
    email = forms.EmailField(label='Correo electrónico')
    nombre_completo = forms.CharField(label='Nombre completo', max_length=150)
    carnet = forms.CharField(label='Carnet', max_length=30)
    telefono = forms.CharField(label='Teléfono', max_length=20, required=False)

    def __init__(self, *args, usuario=None, **kwargs):
        self.usuario = usuario
        if usuario and not args and 'initial' not in kwargs:
            kwargs['initial'] = {
                'username': usuario.username,
                'email': usuario.email,
                'nombre_completo': usuario.perfil.nombre_completo,
                'carnet': usuario.perfil.carnet,
                'telefono': usuario.perfil.telefono,
            }
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exclude(
            pk=self.usuario.pk if self.usuario else None
        ).exists():
            raise forms.ValidationError('Este nombre de usuario ya está registrado.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(
            pk=self.usuario.pk if self.usuario else None
        ).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return email

    def clean_carnet(self):
        carnet = self.cleaned_data['carnet'].strip()
        if PerfilUsuario.objects.filter(carnet__iexact=carnet).exclude(
            user=self.usuario if self.usuario else None
        ).exists():
            raise forms.ValidationError('Este carnet ya está registrado.')
        return carnet
