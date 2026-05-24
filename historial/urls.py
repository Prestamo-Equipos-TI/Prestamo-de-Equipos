from django.urls import path

from .views import (
    historial_inicio,
    historial_usuarios, 
    historial_usuario_detalle,
    historial_equipos,
    historial_equipo_detalle,
)

app_name = 'historial'

urlpatterns = [
    path('', historial_inicio, name='inicio'),
    path('usuarios/', historial_usuarios, name='usuarios'),
    path('usuarios/<int:usuario_id>/',historial_usuario_detalle,name='usuario_detalle'),
    path('equipos/',historial_equipos,name='equipos'),
    path('equipos/<int:equipo_id>/',historial_equipo_detalle,name='equipo_detalle'),
]