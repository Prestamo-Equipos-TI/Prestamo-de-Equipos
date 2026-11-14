from django.contrib.admin.apps import AdminConfig


class AdminEmergenciaConfig(AdminConfig):
    default_site = 'config.admin_site.AdminEmergenciaSite'
