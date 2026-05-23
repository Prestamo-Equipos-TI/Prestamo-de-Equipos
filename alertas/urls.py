from django.urls import path
from .views import alertas_lista

app_name = 'alertas'

urlpatterns = [
    path('', alertas_lista, name='lista'),
]