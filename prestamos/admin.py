from django.contrib import admin
from .models import SolicitudPrestamo


@admin.register(SolicitudPrestamo)
class SolicitudPrestamoAdmin(admin.ModelAdmin):
    list_display = (
        'usuario',
        'equipo',
        'fecha_prestamo',
        'estado',
        'fecha_solicitud',
    )

    list_filter = (
        'estado',
        'fecha_prestamo',
    )

    search_fields = (
        'usuario__username',
        'usuario__email',
        'equipo__codigo',
        'equipo__nombre',
    )