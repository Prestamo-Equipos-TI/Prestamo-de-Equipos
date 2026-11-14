from secrets import token_urlsafe

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import UsuarioGestionForm
from .permisos import roles_gestionables, solo_gestor_ti
from .models import PerfilUsuario, RegistroGestionUsuario

from alertas.models import Alerta
from inventario.models import Equipo
from prestamos.models import SolicitudPrestamo


@login_required
def dashboard(request):
    # Verifica si el usuario tiene alertas no leídas para mostrar badge
    hoy = timezone.localdate()

    context = {
        'active_page': 'dashboard',
        'content_template': 'pages/dashboard_content.html',

        # ==========================================
        # ALERTAS
        # ==========================================

        'tiene_alertas_nuevas': Alerta.objects.filter(
            usuario=request.user,
            leida=False
        ).exists(),

        # ==========================================
        # ESTADÍSTICAS DEL INVENTARIO
        # ==========================================

        'total_equipos': Equipo.objects.filter(
            activo=True
        ).count(),

        'equipos_disponibles': Equipo.objects.filter(
            activo=True,
            estado='disponible'
        ).count(),

        'equipos_prestados': Equipo.objects.filter(
            activo=True,
            estado='prestado'
        ).count(),

        'equipos_reservados': Equipo.objects.filter(
            activo=True,
            estado='reservado'
        ).count(),

        'equipos_averiados': Equipo.objects.filter(
            activo=True,
            estado='averiado'
        ).count(),

        'equipos_mantenimiento': Equipo.objects.filter(
            activo=True,
            estado='mantenimiento'
        ).count(),

        # ==========================================
        # ESTADÍSTICAS DE PRÉSTAMOS
        # ==========================================

        'solicitudes_pendientes': SolicitudPrestamo.objects.filter(
            estado=SolicitudPrestamo.ESTADO_PENDIENTE
        ).count(),

        'prestamos_vencidos': SolicitudPrestamo.objects.filter(
            estado__in=(SolicitudPrestamo.ESTADO_ENTREGADO,
                        SolicitudPrestamo.ESTADO_CANCELACION_PENDIENTE),
            fecha_devolucion_estimada__lt=hoy,
            fecha_devolucion_real__isnull=True
        ).count(),
    }

    # ==========================================
    # RESPUESTA HTMX
    # ==========================================

    if request.headers.get('HX-Request'):
        return render(
            request,
            'pages/dashboard_content.html',
            context
        )

    # ==========================================
    # CARGA NORMAL DEL DASHBOARD
    # ==========================================

    return render(
        request,
        'pages/app_layout.html',
        context
    )


def _usuario_gestionable(actor, usuario_id):
    return get_object_or_404(
        User.objects.select_related('perfil'),
        pk=usuario_id,
        perfil__rol__in=roles_gestionables(actor),
        is_staff=False,
        is_superuser=False,
    )


def _render_panel(request, plantilla, contexto, status=200):
    contexto['active_page'] = 'usuarios'
    if request.headers.get('HX-Request'):
        return render(request, plantilla, contexto, status=status)
    contexto['content_template'] = plantilla
    return render(request, 'pages/app_layout.html', contexto, status=status)


@login_required
@solo_gestor_ti
def usuarios_lista(request):
    busqueda = request.GET.get('q', '').strip()
    usuarios = User.objects.select_related('perfil').filter(
        perfil__rol__in=roles_gestionables(request.user),
        is_staff=False,
        is_superuser=False,
    ).order_by('perfil__nombre_completo')
    if busqueda:
        usuarios = usuarios.filter(
            Q(username__icontains=busqueda)
            | Q(email__icontains=busqueda)
            | Q(perfil__nombre_completo__icontains=busqueda)
            | Q(perfil__carnet__icontains=busqueda)
        )
    if request.headers.get('HX-Request') and request.GET.get('partial') == 'tabla':
        return render(request, 'pages/usuarios/tabla.html', {
            'usuarios': usuarios,
            'busqueda': busqueda,
        })
    return _render_panel(request, 'pages/usuarios/lista_content.html', {
        'usuarios': usuarios,
        'busqueda': busqueda,
    })


@login_required
@solo_gestor_ti
def usuario_detalle(request, usuario_id):
    usuario = _usuario_gestionable(request.user, usuario_id)
    return _render_panel(request, 'pages/usuarios/detalle_content.html', {
        'usuario_gestionado': usuario,
        'acciones': usuario.gestiones_recibidas.select_related('actor')[:10],
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
@solo_gestor_ti
@never_cache
def usuario_crear(request):
    roles = roles_gestionables(request.user)
    form = UsuarioGestionForm(request.POST if request.method == 'POST' else None, roles_permitidos=roles)
    if request.method == 'POST' and form.is_valid():
        clave = token_urlsafe(24)
        with transaction.atomic():
            usuario = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=clave,
            )
            PerfilUsuario.objects.create(
                user=usuario,
                rol=form.cleaned_data['rol'],
                nombre_completo=form.cleaned_data['nombre_completo'],
                carnet=form.cleaned_data['carnet'],
                telefono=form.cleaned_data['telefono'],
                debe_cambiar_clave=True,
            )
            RegistroGestionUsuario.objects.create(
                actor=request.user, usuario=usuario, accion='crear',
                rol_nuevo=form.cleaned_data['rol'],
            )
        return _render_panel(request, 'pages/usuarios/resultado_content.html', {
            'usuario_gestionado': usuario,
            'clave': clave,
            'accion': 'crear',
            'es_modal': bool(request.headers.get('HX-Request')),
        })
    return _render_panel(request, 'pages/usuarios/formulario_content.html', {
        'form': form,
        'titulo': 'Registrar usuario' if len(roles) > 1 else 'Registrar solicitante',
        'descripcion': 'Completa los datos de la nueva cuenta.',
        'es_modal': bool(request.headers.get('HX-Request')),
    }, status=422 if request.method == 'POST' and request.headers.get('HX-Request') else 200)


@login_required
@solo_gestor_ti
def usuario_editar(request, usuario_id):
    usuario = _usuario_gestionable(request.user, usuario_id)
    roles = (PerfilUsuario.ROL_SUPERADMIN,) if usuario.perfil.es_principal else roles_gestionables(request.user)
    form = UsuarioGestionForm(request.POST if request.method == 'POST' else None,
                              usuario=usuario, roles_permitidos=roles)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            usuario.username = form.cleaned_data['username']
            usuario.email = form.cleaned_data['email']
            usuario.save(update_fields=['username', 'email'])
            rol_anterior = usuario.perfil.rol
            usuario.perfil.rol = form.cleaned_data['rol']
            usuario.perfil.nombre_completo = form.cleaned_data['nombre_completo']
            usuario.perfil.carnet = form.cleaned_data['carnet']
            usuario.perfil.telefono = form.cleaned_data['telefono']
            usuario.perfil.save(update_fields=['rol', 'nombre_completo', 'carnet', 'telefono'])
            if rol_anterior != usuario.perfil.rol:
                RegistroGestionUsuario.objects.create(
                    actor=request.user, usuario=usuario, accion='cambiar_rol',
                    rol_anterior=rol_anterior, rol_nuevo=usuario.perfil.rol,
                )
            RegistroGestionUsuario.objects.create(
                actor=request.user, usuario=usuario, accion='editar'
            )
        return _render_panel(request, 'pages/usuarios/resultado_content.html', {
            'usuario_gestionado': usuario,
            'accion': 'editar',
            'es_modal': bool(request.headers.get('HX-Request')),
        })
    return _render_panel(request, 'pages/usuarios/formulario_content.html', {
        'form': form,
        'titulo': 'Editar usuario',
        'descripcion': 'Actualiza los datos de la cuenta.',
        'usuario_gestionado': usuario,
        'es_modal': bool(request.headers.get('HX-Request')),
    }, status=422 if request.method == 'POST' and request.headers.get('HX-Request') else 200)


@login_required
@solo_gestor_ti
@require_POST
def usuario_estado(request, usuario_id):
    accion = request.POST.get('accion')
    if accion not in ('activar', 'desactivar'):
        return HttpResponseBadRequest('Acción no válida')
    with transaction.atomic():
        usuario = _usuario_gestionable(request.user, usuario_id)
        usuario = User.objects.select_for_update().select_related('perfil').get(pk=usuario.pk)
        activo = accion == 'activar'
        if not activo and usuario.perfil.es_principal:
            return HttpResponseForbidden('No se puede desactivar al superadministrador principal.')
        if usuario.is_active == activo:
            return HttpResponseBadRequest('La cuenta ya tiene ese estado')
        usuario.is_active = activo
        usuario.save(update_fields=['is_active'])
        RegistroGestionUsuario.objects.create(
            actor=request.user, usuario=usuario, accion=accion
        )
    if request.headers.get('HX-Request'):
        return HttpResponse(status=204)
    messages.success(request, 'Estado de la cuenta actualizado.')
    return redirect('usuarios_lista')


@login_required
@solo_gestor_ti
@require_POST
@never_cache
def usuario_restablecer_clave(request, usuario_id):
    usuario = _usuario_gestionable(request.user, usuario_id)
    clave = token_urlsafe(24)
    with transaction.atomic():
        usuario.set_password(clave)
        usuario.save(update_fields=['password'])
        usuario.perfil.debe_cambiar_clave = True
        usuario.perfil.save(update_fields=['debe_cambiar_clave'])
        RegistroGestionUsuario.objects.create(
            actor=request.user, usuario=usuario, accion='restablecer_clave'
        )
    return _render_panel(request, 'pages/usuarios/resultado_content.html', {
        'usuario_gestionado': usuario,
        'clave': clave,
        'accion': 'restablecer_clave',
        'es_modal': bool(request.headers.get('HX-Request')),
    })


@login_required
def cambiar_clave(request):
    form = PasswordChangeForm(request.user, request.POST if request.method == 'POST' else None)
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        perfil = getattr(usuario, 'perfil', None)
        if perfil and perfil.debe_cambiar_clave:
            perfil.debe_cambiar_clave = False
            perfil.save(update_fields=['debe_cambiar_clave'])
        update_session_auth_hash(request, usuario)
        messages.success(request, 'Contraseña actualizada correctamente.')
        return redirect('cambiar_clave')
    return render(request, 'pages/app_layout.html', {
        'active_page': 'cambiar_clave',
        'content_template': 'pages/usuarios/cambiar_clave_content.html',
        'form': form,
    })
