from django.urls import path
from .views import (
    inventario_lista,
    equipo_crear,
    equipo_editar,
    equipo_detalle,
    equipo_desactivar,
)

app_name = 'inventario'

urlpatterns = [
    path('', inventario_lista, name='lista'),
    path('registrar/', equipo_crear, name='crear'),
    path('editar/<int:equipo_id>/', equipo_editar, name='editar'),
    path('detalle/<int:equipo_id>/', equipo_detalle, name='detalle'),
    path('desactivar/<int:equipo_id>/', equipo_desactivar, name='desactivar'),
]