from django.urls import path

from .views import (
    reportar_averia_lista,
    reportar_averia_modal,
    confirmar_reporte_averia,
    averias_admin_inicio,
    averias_admin_lista,
    reporte_administrativo_lista,
    reporte_administrativo_modal,
    confirmar_reporte_administrativo,
    gestionar_averia_modal,
    confirmar_gestion_averia,
    resolver_averia_modal,
    confirmar_resolucion_averia,
)

app_name = 'averias'

urlpatterns = [
    path(
        '',
        averias_admin_inicio,
        name='admin_inicio'
    ),

    path(
        'reportes/',
        averias_admin_lista,
        name='admin_lista'
    ),

    path(
        'reporte-administrativo/',
        reporte_administrativo_lista,
        name='reporte_administrativo'
    ),

    path(
        'reporte-administrativo/<int:equipo_id>/',
        reporte_administrativo_modal,
        name='reporte_administrativo_modal'
    ),

    path(
        'reporte-administrativo/<int:equipo_id>/confirmar/',
        confirmar_reporte_administrativo,
        name='confirmar_reporte_administrativo'
    ),

    path(
        'reportar/',
        reportar_averia_lista,
        name='reportar'
    ),

    path(
        'reportar/<int:solicitud_id>/',
        reportar_averia_modal,
        name='reportar_modal'
    ),

    path(
        'reportar/<int:solicitud_id>/confirmar/',
        confirmar_reporte_averia,
        name='confirmar_reporte'
    ),
    path(
    'reportes/<int:reporte_id>/gestionar/',
    gestionar_averia_modal,
    name='gestionar_modal'
    ),

    path(
    'reportes/<int:reporte_id>/gestionar/confirmar/',
    confirmar_gestion_averia,
    name='confirmar_gestion'
    ),
    path(
    'reportes/<int:reporte_id>/resolver/',
    resolver_averia_modal,
    name='resolver_modal'
    ),

    path(
    'reportes/<int:reporte_id>/resolver/confirmar/',
    confirmar_resolucion_averia,
    name='confirmar_resolucion'
    ),

]