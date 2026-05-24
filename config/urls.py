from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
    path('inventario/', include('inventario.urls')),
    path('prestamos/', include('prestamos.urls')),
    path('alertas/', include('alertas.urls')),
    path('averias/', include('averias.urls')),
]