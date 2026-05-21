from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import EquipoForm


@login_required
def inventario_lista(request):
    return render(request, 'pages/inventario/lista.html')


@login_required
def equipo_crear(request):
    es_htmx = request.headers.get('HX-Request')

    if request.method == 'POST':
        form = EquipoForm(request.POST)

        if form.is_valid():
            form.save()

            if es_htmx:
                return render(request, 'pages/inventario/formulario.html', {
                    'form': EquipoForm(),
                    'es_modal': True,
                    'guardado': True,
                })

            return redirect('inventario:lista')
    else:
        form = EquipoForm()

    return render(request, 'pages/inventario/formulario.html', {
        'form': form,
        'es_modal': bool(es_htmx),
        'guardado': False,
    })