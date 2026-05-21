from django.contrib import admin
from .models import Equipo


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'nombre',
        'categoria',
        'marca',
        'estado',
        'ubicacion',
        'fecha_registro',
    )

    list_filter = (
        'categoria',
        'estado',
        'marca',
    )

    search_fields = (
        'codigo',
        'nombre',
        'marca',
        'modelo',
        'numero_serie',
    )