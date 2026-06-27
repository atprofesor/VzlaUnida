from django.db import models
from django.contrib.auth.models import User

class Huesped(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True) # <--- Agrega null=True, blank=True
    # Datos de contacto adicionales
    telefono = models.CharField(max_length=20) 
    
    # Ubicación
    ciudad = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    
    # Capacidades
    capacidad_ninos = models.IntegerField(default=0)
    capacidad_adultos = models.IntegerField(default=0)
    capacidad_adultos_mayores = models.IntegerField(default=0)
    
    # Mascotas
    acepta_mascotas_pequenas = models.BooleanField(default=False)
    acepta_mascotas_medianas = models.BooleanField(default=False)
    acepta_mascotas_grandes = models.BooleanField(default=False)
    
    # Detalles adicionales
    tipo_acogida = models.CharField(max_length=50) # ej: temporal, indefinida
    tiempo_disponible_meses = models.IntegerField(default=1)
    
    # Archivos (Seguridad)
    cedula_file = models.FileField(upload_to='documentos/cedulas/')
    residencia_file = models.FileField(upload_to='documentos/residencia/')
    
    # Verificación y control de intentos
    estado_verificacion = models.CharField(max_length=20, default='pendiente')
    intentos_fallidos = models.IntegerField(default=0)
    verificado_manualmente = models.BooleanField(default=False)

    def __str__(self):
        return f"Huésped: {self.user.username}"

class Afectado(models.Model):
    # Datos de contacto
    nombre_completo = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    
    cantidad_familiares = models.IntegerField(default=1)
    documento_afectado = models.FileField(upload_to='documentos/afectados/', null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    esta_reubicado = models.BooleanField(default=False)

    def __str__(self):
        return f"Afectado: {self.nombre_completo}"