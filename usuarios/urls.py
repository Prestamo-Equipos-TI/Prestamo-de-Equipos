from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import (
    dashboard, usuarios_lista, usuario_detalle, usuario_crear,
    usuario_editar, usuario_estado, usuario_restablecer_clave, cambiar_clave,
)

urlpatterns = [
    path('usuarios/', usuarios_lista, name='usuarios_lista'),
    path('usuarios/crear/', usuario_crear, name='usuario_crear'),
    path('usuarios/<int:usuario_id>/', usuario_detalle, name='usuario_detalle'),
    path('usuarios/<int:usuario_id>/editar/', usuario_editar, name='usuario_editar'),
    path('usuarios/<int:usuario_id>/estado/', usuario_estado, name='usuario_estado'),
    path('usuarios/<int:usuario_id>/restablecer-clave/', usuario_restablecer_clave, name='usuario_restablecer_clave'),
    path('cuenta/cambiar-clave/', cambiar_clave, name='cambiar_clave'),
    path(
        '',
        LoginView.as_view(
            template_name='pages/login.html',
            redirect_authenticated_user=True
        ),
        name='login'
    ),

    path(
        'dashboard/',
        dashboard,
        name='dashboard'
    ),

    path(
        'logout/',
        LogoutView.as_view(next_page='login'),
        name='logout'
    ),
]
