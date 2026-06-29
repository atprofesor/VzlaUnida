from django.db import models
from django.contrib.auth.models import User

# ✅ TODOS LOS ESTADOS DE VENEZUELA
UBICACIONES = {
    'Amazonas': ['Puerto Ayacucho'],
    'Anzoátegui': ['Barcelona', 'Puerto La Cruz', 'Lechería', 'El Tigre', 'Anaco', 'Cantaura'],
    'Apure': ['San Fernando de Apure', 'Guasdualito'],
    'Aragua': ['Maracay', 'Turmero', 'El Limón', 'La Victoria', 'Cagua', 'Villa de Cura'],
    'Barinas': ['Barinas', 'Sabaneta', 'Ciudad Bolivia'],
    'Bolívar': ['Ciudad Guayana', 'Ciudad Bolívar', 'Upata', 'El Callao'],
    'Carabobo': ['Valencia', 'Naguanagua', 'San Diego', 'Guacara', 'Puerto Cabello', 'Mariara'],
    'Cojedes': ['San Carlos', 'Tinaquillo'],
    'Delta Amacuro': ['Tucupita'],
    'Distrito Capital': ['Caracas'],
    'Falcón': ['Coro', 'Punto Fijo', 'Pueblo Nuevo'],
    'Guárico': ['San Juan de los Morros', 'Calabozo', 'Valle de la Pascua', 'Zaraza'],
    'Lara': ['Barquisimeto', 'Cabudare', 'Carora', 'El Tocuyo'],
    'Mérida': ['Mérida', 'Ejido', 'Tovar', 'El Vigía'],
    'Miranda': ['Los Teques', 'Guarenas', 'Guatire', 'Ocumare del Tuy', 'Santa Teresa del Tuy', 'Charallave'],
    'Monagas': ['Maturín', 'Punta de Mata', 'Temblador'],
    'Nueva Esparta': ['Porlamar', 'La Asunción', 'Juan Griego'],
    'Portuguesa': ['Guanare', 'Acarigua', 'Araure'],
    'Sucre': ['Cumaná', 'Carúpano', 'Güiria'],
    'Táchira': ['San Cristóbal', 'Táriba', 'Rubio', 'La Fría'],
    'Trujillo': ['Trujillo', 'Valera', 'Boconó'],
    'La Guaira': ['La Guaira', 'Macuto', 'Caraballeda'],
    'Yaracuy': ['San Felipe', 'Chivacoa', 'Yaritagua'],
    'Zulia': ['Maracaibo', 'Cabimas', 'Ciudad Ojeda', 'Santa Rita', 'La Villa del Rosario'],
}

TIPO_ACOGIDA_CHOICES = [
    ('Habitacion(es)', 'Habitación(es)'),
    ('Anexo independiente', 'Anexo independiente'),
    ('Vivienda completa', 'Vivienda completa'),
]

class Huesped(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    nombres = models.CharField(max_length=100, default='')
    apellidos = models.CharField(max_length=100, default='')
    
    # ✅ CÉDULA CON PREFIJO Y NÚMERO
    prefijo_cedula = models.CharField(max_length=1, choices=[('V', 'V'), ('E', 'E')], default='V')
    numero_cedula = models.CharField(max_length=20, default='')
    
    telefono = models.CharField(max_length=20, default='')
    ciudad = models.CharField(max_length=100, default='')
    estado = models.CharField(max_length=100, default='')
    sector = models.CharField(max_length=300, default='')
    capacidad_ninos = models.IntegerField(default=0)
    capacidad_adultos = models.IntegerField(default=0)
    capacidad_adultos_mayores = models.IntegerField(default=0)
    acepta_mascotas_pequenas = models.BooleanField(default=False)
    acepta_mascotas_medianas = models.BooleanField(default=False)
    acepta_mascotas_grandes = models.BooleanField(default=False)
    tipo_acogida = models.CharField(max_length=50, choices=TIPO_ACOGIDA_CHOICES, default='Habitacion(es)')
    tiempo_disponible_meses = models.IntegerField(default=1)
    cedula_file = models.FileField(upload_to='documentos/cedulas/', blank=False)
    residencia_file = models.FileField(upload_to='documentos/residencia/', blank=False)
    estado_verificacion = models.CharField(max_length=20, default='pendiente')

    def capacidad_total(self):
        """Calcula la capacidad total de personas que puede albergar"""
        return self.capacidad_ninos + self.capacidad_adultos + self.capacidad_adultos_mayores
    
    def cedula_completa(self):
        """Retorna la cédula completa con prefijo y número"""
        return f"{self.prefijo_cedula}-{self.numero_cedula}"
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.cedula_completa()})"

class Afectado(models.Model):
    nombre_completo = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20, default='')
    ciudad = models.CharField(max_length=100, default='')
    estado = models.CharField(max_length=100, default='')
    
    def __str__(self):
        return f"Afectado: {self.nombre_completo}"