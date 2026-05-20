from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import dashboard

urlpatterns = [
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