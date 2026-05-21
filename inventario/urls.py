from django.urls import path
from .views import inventario_lista

app_name = 'inventario'

urlpatterns = [
    path('', inventario_lista, name='lista'),
]