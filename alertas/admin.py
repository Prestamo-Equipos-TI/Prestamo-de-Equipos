from django.contrib import admin
from .models import Alerta


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = (
        'usuario',
        'titulo',
        'tipo',
        'leida',
        'fecha_creacion',
    )

    list_filter = (
        'tipo',
        'leida',
        'fecha_creacion',
    )

    search_fields = (
        'usuario__username',
        'usuario__email',
        'titulo',
        'mensaje',
    )