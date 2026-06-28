from django.db import models
from django.contrib.auth.models import User

# Diccionario de ubicaciones para el sistema
UBICACIONES = {
    'Anzoategui': ['Lecheria', 'Barcelona', 'Puerto La Cruz', 'El Tigre'],
    'Miranda': ['Caracas', 'Los Teques', 'Guarenas'],
    'Carabobo': ['Valencia', 'Naguanagua', 'San Diego'],
    # Puedes añadir el resto de los estados aquí
}

TIPO_ACOGIDA_CHOICES = [
    ('Habitacion(es)', 'Habitación(es)'),
    ('Anexo independiente', 'Anexo independiente'),
    ('Vivienda completa', 'Vivienda completa'),
]

class Huesped(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Datos de contacto
    telefono = models.CharField(max_length=20) 
    
    # Ubicación (Guardamos el nombre del estado y la ciudad)
    ciudad = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    sector = models.CharField(max_length=300)
    
    # ... resto de campos igual (capacidades, mascotas, etc.)
    capacidad_ninos = models.IntegerField(default=0, verbose_name="Capacidad niños")
    capacidad_adultos = models.IntegerField(default=0)
    capacidad_adultos_mayores = models.IntegerField(default=0)
    acepta_mascotas_pequenas = models.BooleanField(default=False)
    acepta_mascotas_medianas = models.BooleanField(default=False)
    acepta_mascotas_grandes = models.BooleanField(default=False)
    tipo_acogida = models.CharField(
        max_length=50, 
        choices=TIPO_ACOGIDA_CHOICES
    )
    
    
    tiempo_disponible_meses = models.IntegerField(default=1)
    cedula_file = models.FileField(upload_to='documentos/cedulas/')
    residencia_file = models.FileField(upload_to='documentos/residencia/')
    estado_verificacion = models.CharField(max_length=20, default='pendiente')
    intentos_fallidos = models.IntegerField(default=0)
    verificado_manualmente = models.BooleanField(default=False)

    def __str__(self):
        if self.user:
            return f"Huésped: {self.user.username}"
        return f"Huésped (ID: {self.id})"

class Afectado(models.Model):
    # ... todos tus campos ...
    nombre_completo = models.CharField(max_length=200)
    # ...
    def __str__(self):
        return f"Afectado: {self.nombre_completo}"