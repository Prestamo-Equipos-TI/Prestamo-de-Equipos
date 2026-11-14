from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError


class AccesoTecnicoForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser:
            raise ValidationError(
                'El acceso a Django Admin está reservado a cuentas técnicas de emergencia.',
                code='sin_acceso_tecnico',
            )


class AdminEmergenciaSite(AdminSite):
    site_header = 'Control IT · Administración técnica'
    site_title = 'Acceso técnico de emergencia'
    index_title = 'Administración técnica de emergencia'
    login_form = AccesoTecnicoForm

    def has_permission(self, request):
        user = request.user
        return user.is_active and user.is_staff and user.is_superuser
