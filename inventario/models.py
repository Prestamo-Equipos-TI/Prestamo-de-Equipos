from django.db import models


class Equipo(models.Model):
    CATEGORIAS = [
        ('laptop', 'Laptop'),
        ('proyector', 'Proyector'),
        ('tablet', 'Tablet'),
        ('accesorio', 'Accesorio'),
        ('otro', 'Otro'),
    ]

    ESTADOS = [
        ('disponible', 'Disponible'),
        ('prestado', 'Prestado'),
        ('averiado', 'Averiado'),
        ('mantenimiento', 'Mantenimiento'),
    ]

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True, unique=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    ubicacion = models.CharField(max_length=100)
    observaciones = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'