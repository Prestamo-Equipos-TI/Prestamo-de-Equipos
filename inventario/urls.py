from django.urls import path
from .views import inventario_lista, equipo_crear

app_name = 'inventario'

urlpatterns = [
    path('', inventario_lista, name='lista'),
    path('registrar/', equipo_crear, name='crear'),
]