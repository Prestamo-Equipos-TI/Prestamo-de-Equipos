from django.contrib import admin
from django.urls import path, include
from config.views import error_500


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
    path('inventario/', include('inventario.urls')),
    path('prestamos/', include('prestamos.urls')),
    path('alertas/', include('alertas.urls')),
    path('averias/', include('averias.urls')),
    path('historial/', include('historial.urls')),
]

handler500 = error_500