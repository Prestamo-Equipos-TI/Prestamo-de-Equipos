from django.urls import path
from .views import (
    solicitar_prestamo_lista,
    crear_solicitud_prestamo,
    mis_solicitudes,
    solicitudes_admin,
    prestamos_admin_inicio,
    aprobar_solicitud_modal,
    confirmar_aprobacion_solicitud,
    rechazar_solicitud,
    entregas_lista,
    registrar_entrega_modal,
    confirmar_entrega,
    equipos_prestados,
    detalle_prestamo,
)

app_name = 'prestamos'

urlpatterns = [
    path(
        '',
        prestamos_admin_inicio,
        name='admin_inicio'
    ),

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

    path(
        'solicitudes/',
        solicitudes_admin,
        name='solicitudes_admin'
    ),
    path(
    'solicitudes/<int:solicitud_id>/aprobar/',
    aprobar_solicitud_modal,
    name='aprobar_modal'
),

    path(
    'solicitudes/<int:solicitud_id>/aprobar/confirmar/',
    confirmar_aprobacion_solicitud,
    name='confirmar_aprobacion'
),
    path(
    'solicitudes/<int:solicitud_id>/rechazar/',
    rechazar_solicitud,
    name='rechazar'
),
path(
    'entregas/',
    entregas_lista,
    name='entregas'
),

path(
    'entregas/<int:solicitud_id>/registrar/',
    registrar_entrega_modal,
    name='registrar_entrega_modal'
),

path(
    'entregas/<int:solicitud_id>/confirmar/',
    confirmar_entrega,
    name='confirmar_entrega'
),
path(
    'equipos-prestados/',
    equipos_prestados,
    name='equipos_prestados'
),
path(
    'equipos-prestados/<int:solicitud_id>/detalle/',
    detalle_prestamo,
    name='detalle_prestamo'
),
]