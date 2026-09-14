from django.urls import path

from .views import (
    alertas_lista,
    alerta_nueva,
)


app_name = 'alertas'


urlpatterns = [
    path(
        '',
        alertas_lista,
        name='lista'
    ),

    path(
        'nueva/',
        alerta_nueva,
        name='nueva'
    ),
]