from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse


class ExigirCambioClaveMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            perfil = getattr(request.user, 'perfil', None)
            if perfil and perfil.debe_cambiar_clave and request.path not in (
                reverse('cambiar_clave'), reverse('logout')
            ):
                if request.headers.get('HX-Request'):
                    respuesta = HttpResponse(status=204)
                    respuesta['HX-Redirect'] = reverse('cambiar_clave')
                    return respuesta
                return redirect('cambiar_clave')
        return self.get_response(request)
