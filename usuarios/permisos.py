from functools import wraps

from django.http import HttpResponseForbidden

from .models import PerfilUsuario


def rol_funcional(usuario):
    if not usuario.is_authenticated or not usuario.is_active:
        return None
    perfil = getattr(usuario, 'perfil', None)
    return perfil.rol if perfil else None


def es_principal(usuario):
    perfil = getattr(usuario, 'perfil', None)
    return bool(
        rol_funcional(usuario) == PerfilUsuario.ROL_SUPERADMIN
        and perfil.es_principal
    )


def roles_gestionables(usuario):
    rol = rol_funcional(usuario)
    if rol == PerfilUsuario.ROL_ADMIN_TI:
        return (PerfilUsuario.ROL_USUARIO,)
    if rol == PerfilUsuario.ROL_SUPERADMIN:
        roles = (PerfilUsuario.ROL_USUARIO, PerfilUsuario.ROL_ADMIN_TI)
        if es_principal(usuario):
            return roles + (PerfilUsuario.ROL_SUPERADMIN,)
        return roles
    return ()


def solo_gestor_ti(vista):
    @wraps(vista)
    def protegida(request, *args, **kwargs):
        if rol_funcional(request.user) not in (
            PerfilUsuario.ROL_ADMIN_TI, PerfilUsuario.ROL_SUPERADMIN
        ):
            return HttpResponseForbidden('Acceso reservado a gestión TI')
        return vista(request, *args, **kwargs)
    return protegida


def solo_solicitante(vista):
    @wraps(vista)
    def protegida(request, *args, **kwargs):
        if rol_funcional(request.user) != PerfilUsuario.ROL_USUARIO:
            return HttpResponseForbidden('Acceso reservado a solicitantes')
        return vista(request, *args, **kwargs)
    return protegida
