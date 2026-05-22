from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from .forms import EquipoForm
from .models import Equipo


@login_required
def inventario_lista(request):
    equipos = Equipo.objects.all().order_by('-fecha_registro')

    context = {
        'active_page': 'inventario',
        'content_template': 'pages/inventario/lista_content.html',
        'equipos': equipos,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'pages/inventario/lista_content.html', context)

    return render(request, 'pages/app_layout.html', context)


@login_required
def equipo_crear(request):
    es_htmx = request.headers.get('HX-Request')

    if request.method == 'POST':
        form = EquipoForm(request.POST)

        if form.is_valid():
            form.save()

            if es_htmx:
                return HttpResponse(status=204)

            return redirect('inventario:lista')

        if es_htmx:
            return render(request, 'pages/inventario/formulario.html', {
                'form': form,
                'es_modal': True,
                'guardado': False,
            }, status=422)

    else:
        form = EquipoForm()

    return render(request, 'pages/inventario/formulario.html', {
        'form': form,
        'es_modal': bool(es_htmx),
        'guardado': False,
    })

@login_required
def equipo_editar(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)
    es_htmx = request.headers.get('HX-Request')

    if request.method == 'POST':
        form = EquipoForm(request.POST, instance=equipo)

        if form.is_valid():
            form.save()

            if es_htmx:
                return HttpResponse(status=204)

            return redirect('inventario:lista')

        if es_htmx:
            return render(request, 'pages/inventario/formulario.html', {
                'form': form,
                'es_modal': True,
                'modo': 'editar',
                'equipo': equipo,
            }, status=422)

    else:
        form = EquipoForm(instance=equipo)

    return render(request, 'pages/inventario/formulario.html', {
        'form': form,
        'es_modal': bool(es_htmx),
        'modo': 'editar',
        'equipo': equipo,
    })