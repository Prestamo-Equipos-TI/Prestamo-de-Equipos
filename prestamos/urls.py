from django.urls import path
from .views import (
    solicitar_prestamo_lista,
    crear_solicitud_prestamo,
    mis_solicitudes,
)

app_name = 'prestamos'

urlpatterns = [
    path(
        'solicitar/',
        solicitar_prestamo_lista,
        name='solicitar'
    ),

    path(
        'solicitar/<int:equipo_id>/',
        crear_solicitud_prestamo,
        name='crear'
    ),

    path(
        'mis-solicitudes/',
        mis_solicitudes,
        name='mis_solicitudes'
    ),
]