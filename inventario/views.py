from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def inventario_lista(request):
    return render(request, 'pages/inventario/lista.html')