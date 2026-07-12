from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# ✅ ESTADOS DE VERIFICACIÓN
ESTADO_VERIFICACION_CHOICES = [
    ('pendiente', '⏳ Pendiente de revisión'),
    ('en_revision', '🔍 En revisión'),
    ('aprobado', '✅ Aprobado'),
    ('rechazado', '❌ Rechazado'),
    ('requiere_correccion', '📝 Requiere corrección'),
]

# ✅ TODOS LOS ESTADOS DE VENEZUELA CON CIUDADES AMPLIADAS
UBICACIONES = {
    'Amazonas': [
        'Puerto Ayacucho', 'San Fernando de Atabapo', 'San Carlos de Río Negro',
        'Maroa', 'La Esmeralda'
    ],
    'Anzoátegui': [
        'Barcelona', 'Puerto La Cruz', 'Lechería', 'El Tigre', 'Anaco',
        'Cantaura', 'Guanta', 'Boca de Uchire', 'Pariaguán', 'Aragua de Barcelona',
        'Clarines', 'Soledad', 'San José de Guanipa', 'Onoto'
    ],
    'Apure': [
        'San Fernando de Apure', 'Guasdualito', 'Achaguas', 'Biruaca',
        'Elorza', 'Mantecal', 'Puerto Páez', 'Cunaviche'
    ],
    'Aragua': [
        'Maracay', 'Turmero', 'La Victoria', 'Cagua', 'Villa de Cura',
        'El Limón', 'Palo Negro', 'Santa Rita', 'San Mateo', 'El Consejo',
        'Ocumare de la Costa', 'Choroní', 'La Colonia Tovar', 'San Sebastián',
        'Barbacoas', 'Camatagua'
    ],
    'Barinas': [
        'Barinas', 'Sabaneta', 'Barinitas', 'Santa Bárbara', 'Socopó',
        'Ciudad Bolivia', 'Pedraza', 'Alto Barinas', 'Calderas', 'Caparo',
        'La Caramuca', 'Puerto de Nutrias'
    ],
    'Bolívar': [
        'Ciudad Guayana', 'Ciudad Bolívar', 'Upata', 'El Callao',
        'Caicara del Orinoco', 'Tumeremo', 'Santa Elena de Uairén',
        'Las Claritas', 'Guasipati', 'San Félix', 'La Paragua', 'Maripa'
    ],
    'Carabobo': [
        'Valencia', 'Naguanagua', 'San Diego', 'Guacara', 'Puerto Cabello',
        'Mariara', 'Los Guayos', 'Güigüe', 'Morón', 'Bejuma',
        'Montalbán', 'San Joaquín', 'Miranda', 'Patanemo', 'Bárbula',
        'El Palito'
    ],
    'Cojedes': [
        'San Carlos', 'Tinaquillo', 'Tinaco', 'El Pao', 'La Aguadita',
        'Macapo', 'Las Vegas', 'El Baúl'
    ],
    'Delta Amacuro': [
        'Tucupita', 'Curiapo', 'Pedernales', 'La Horqueta',
        'San José de Amacuro', 'Barrancas del Orinoco'
    ],
    'Distrito Capital': [
        'Caracas', 'El Valle', 'La Candelaria', 'San Bernardino',
        'El Paraíso', 'La Pastora', 'Catia', 'San Juan', 'Santa Teresa',
        'El Recreo', 'Sucre'
    ],
    'Falcón': [
        'Coro', 'Punto Fijo', 'Punta Cardón', 'Tucacas', 'Carirubana',
        'La Vela de Coro', 'Chichiriviche', 'Cumarebo', 'Mirimire',
        'Puerto Cumarebo', 'Churuguara', 'Urumaco'
    ],
    'Guárico': [
        'San Juan de los Morros', 'Calabozo', 'Valle de la Pascua',
        'Zaraza', 'Tucupido', 'El Sombrero', 'Santa María de Ipire',
        'Camaguán', 'Las Mercedes', 'Chaguaramas', 'Ortiz',
        'Altagracia de Orituco', 'El Calvario'
    ],
    'Lara': [
        'Barquisimeto', 'Cabudare', 'Carora', 'El Tocuyo', 'Quíbor',
        'Duaca', 'Sarare', 'Sanare', 'Cubiro', 'Siquisique',
        'Aguada Grande', 'Río Claro'
    ],
    'Mérida': [
        'Mérida', 'Ejido', 'Tovar', 'El Vigía', 'Lagunillas',
        'Bailadores', 'Pregonero', 'Santa Elena de Arenales',
        'La Azulita', 'Mucuchíes', 'Mucurubá', 'Santa Cruz de Mora'
    ],
    'Miranda': [
        'Los Teques', 'Guarenas', 'Guatire', 'Ocumare del Tuy',
        'Santa Teresa del Tuy', 'Charallave', 'Cúa', 'San Francisco de Yare',
        'Caucagua', 'Higuerote', 'Río Chico', 'Baruta', 'Carrizal',
        'San Antonio de los Altos', 'El Hatillo', 'Santa Lucía',
        'Petare', 'Los Dos Caminos', 'La Dolorita', 'Filas de Mariche'
    ],
    'Monagas': [
        'Maturín', 'Punta de Mata', 'Temblador', 'Caripito',
        'Jusepín', 'San Antonio de Capayacuar', 'Caicara de Maturín',
        'El Furrial', 'Quiriquire'
    ],
    'Nueva Esparta': [
        'Porlamar', 'La Asunción', 'Juan Griego', 'Pampatar',
        'El Valle del Espíritu Santo', 'San Juan Bautista', 'Boca de Río',
        'Villa Rosa', 'Punta de Piedras'
    ],
    'Portuguesa': [
        'Guanare', 'Acarigua', 'Araure', 'Agua Blanca',
        'Turén', 'Píritu', 'Ospino', 'Biscucuy', 'Guanarito',
        'Villa Bruzual', 'Chabasquén', 'Payara'
    ],
    'Sucre': [
        'Cumaná', 'Carúpano', 'Güiria', 'Cariaco', 'Río Caribe',
        'Cumanacoa', 'Casigua', 'El Pilar', 'Araya', 'San Antonio del Golfo',
        'Marigüitar', 'Yaguaraparo'
    ],
    'Táchira': [
        'San Cristóbal', 'Táriba', 'Rubio', 'La Fría', 'San Antonio del Táchira',
        'La Grita', 'Michelena', 'Capacho Nuevo', 'Capacho Viejo',
        'Queniquea', 'Abejales', 'Pregonero', 'Ureña', 'Colón',
        'San José de Bolívar', 'Palmira'
    ],
    'Trujillo': [
        'Trujillo', 'Valera', 'Boconó', 'Escuque', 'Betijoque',
        'Carache', 'Monay', 'Pampán', 'Pampanito', 'La Puerta',
        'Campo Elías', 'Motatán', 'Sabana Grande', 'San Rafael de Carvajal'
    ],
    'La Guaira': [
        'La Guaira', 'Macuto', 'Caraballeda', 'Catia La Mar',
        'Naiguatá', 'Maiquetía', 'Camurí Grande', 'Carayaca',
        'Los Corales', 'El Junko'
    ],
    'Yaracuy': [
        'San Felipe', 'Chivacoa', 'Yaritagua', 'Nirgua',
        'Cocorote', 'Aroa', 'Urachiche', 'Sucre', 'Guama',
        'Sabana de Parra', 'Salom', 'Bolívar'
    ],
    'Zulia': [
        'Maracaibo', 'Cabimas', 'Ciudad Ojeda', 'Santa Rita',
        'La Villa del Rosario', 'Lagunillas', 'Machiques de Perijá',
        'San Carlos del Zulia', 'Mara', 'La Concepción',
        'San Rafael del Moján', 'El Mene', 'Santa Bárbara del Zulia',
        'Los Puertos de Altagracia', 'Concepción'
    ],
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
    
    prefijo_cedula = models.CharField(max_length=1, choices=[('V', 'V'), ('E', 'E')], default='V')
    numero_cedula = models.CharField(max_length=20, default='')
    
    telefono = models.CharField(max_length=20, default='')
    ciudad = models.CharField(max_length=100, default='')
    estado = models.CharField(max_length=100, default='')
    sector = models.CharField(max_length=300, default='')
    
    cantidad_personas = models.IntegerField(default=0)
    acepta_ninos = models.BooleanField(default=False)
    acepta_adultos = models.BooleanField(default=False)
    acepta_adultos_mayores = models.BooleanField(default=False)
    acepta_mascotas = models.BooleanField(default=False)
    tipo_acogida = models.CharField(max_length=50, choices=TIPO_ACOGIDA_CHOICES, default='Habitacion(es)')
    tiempo_disponible_meses = models.IntegerField(default=1)
    cedula_file = models.FileField(upload_to='documentos/cedulas/', blank=False)
    residencia_file = models.FileField(upload_to='documentos/residencia/', blank=False)
    estado_verificacion = models.CharField(
        max_length=20, 
        choices=ESTADO_VERIFICACION_CHOICES, 
        default='pendiente'
    )
    comentario_verificacion = models.TextField(
        blank=True, 
        null=True,
        help_text="Comentario del administrador sobre la verificación"
    )
    fecha_verificacion = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Fecha en que se realizó la verificación"
    )

    class Meta:
        unique_together = ['prefijo_cedula', 'numero_cedula']
        verbose_name = 'Huésped'
        verbose_name_plural = 'Huéspedes'

    def capacidad_total(self):
        return self.cantidad_personas
    
    def cedula_completa(self):
        return f"{self.prefijo_cedula}-{self.numero_cedula}"
    
    def is_verified(self):
        return self.estado_verificacion == 'aprobado'
    
    def is_pending(self):
        return self.estado_verificacion == 'pendiente'
    
    def get_estado_display(self):
        return dict(ESTADO_VERIFICACION_CHOICES).get(self.estado_verificacion, self.estado_verificacion)
    
    def matches_recibidos(self):
        """Retorna los matches donde este huésped ha sido contactado (por afectados)"""
        return Match.objects.filter(huesped=self).select_related('afectado')

    def matches_pendientes(self):
        """Retorna los matches pendientes de este huésped"""
        return self.matches_recibidos().filter(estado='pendiente')

    def matches_aceptados(self):
        """Retorna los matches aceptados de este huésped"""
        return self.matches_recibidos().filter(estado='aceptado')

    def matches_rechazados(self):
        """Retorna los matches rechazados de este huésped"""
        return self.matches_recibidos().filter(estado='rechazado')
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.cedula_completa()})"


class Afectado(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    nombres = models.CharField(max_length=100, default='')
    apellidos = models.CharField(max_length=100, default='')
    
    prefijo_cedula = models.CharField(max_length=1, choices=[('V', 'V'), ('E', 'E')], default='V')
    numero_cedula = models.CharField(max_length=20, default='')
    
    telefono = models.CharField(max_length=20, default='')
    ciudad = models.CharField(max_length=100, default='')
    estado = models.CharField(max_length=100, default='')
    sector = models.CharField(max_length=300, default='')
    direccion_anterior = models.TextField(default='', help_text="Dirección donde vivía antes del terremoto")
    
    cantidad_ninos = models.IntegerField(default=0, help_text="Cantidad de niños en el núcleo familiar (menor de 18 años)")
    cantidad_adultos = models.IntegerField(default=0, help_text="Cantidad de adultos en el núcleo familiar")
    cantidad_adultos_mayores = models.IntegerField(default=0, help_text="Cantidad de adultos mayores en el núcleo familiar (mayor a 65 años)")
    tiene_mascotas = models.BooleanField(default=False, help_text="Indica si el núcleo familiar tiene mascotas")
    
    cedula_file = models.FileField(upload_to='documentos/cedulas_afectados/', blank=False)
    residencia_file = models.FileField(upload_to='documentos/residencia_afectados/', blank=False)
    
    estado_verificacion = models.CharField(
        max_length=20, 
        choices=ESTADO_VERIFICACION_CHOICES, 
        default='pendiente'
    )
    comentario_verificacion = models.TextField(
        blank=True, 
        null=True,
        help_text="Comentario del administrador sobre la verificación"
    )
    fecha_verificacion = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Fecha en que se realizó la verificación"
    )

    class Meta:
        unique_together = ['prefijo_cedula', 'numero_cedula']
        verbose_name = 'Afectado'
        verbose_name_plural = 'Afectados'

    def cantidad_total(self):
        """Calcula la cantidad total de personas en el núcleo familiar"""
        return self.cantidad_ninos + self.cantidad_adultos + self.cantidad_adultos_mayores
    
    def cedula_completa(self):
        return f"{self.prefijo_cedula}-{self.numero_cedula}"
    
    def is_verified(self):
        return self.estado_verificacion == 'aprobado'
    
    def is_pending(self):
        return self.estado_verificacion == 'pendiente'
    
    def get_estado_display(self):
        return dict(ESTADO_VERIFICACION_CHOICES).get(self.estado_verificacion, self.estado_verificacion)
    
    def matches_recibidos(self):
        """Retorna los matches donde este afectado ha sido contactado (por huéspedes)"""
        return Match.objects.filter(afectado=self).select_related('huesped')

    def matches_pendientes(self):
        """Retorna los matches pendientes de este afectado"""
        return self.matches_recibidos().filter(estado='pendiente')

    def matches_aceptados(self):
        """Retorna los matches aceptados de este afectado"""
        return self.matches_recibidos().filter(estado='aceptado')
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.cedula_completa()})"


class Match(models.Model):
    ESTADO_MATCH_CHOICES = [
        ('pendiente', '⏳ Pendiente'),
        ('aceptado', '✅ Aceptado'),
        ('rechazado', '❌ Rechazado'),
    ]
    
    huesped = models.ForeignKey(Huesped, on_delete=models.CASCADE, related_name='matches_enviados')
    afectado = models.ForeignKey(Afectado, on_delete=models.CASCADE, related_name='matches_recibidos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(max_length=20, choices=ESTADO_MATCH_CHOICES, default='pendiente')
    mensaje = models.TextField(blank=True, null=True, help_text="Mensaje opcional del huésped al afectado")
    
    # ✅ NUEVO CAMPO: Comentario para almacenar motivo de rechazo
    comentario = models.TextField(blank=True, null=True, help_text="Comentario sobre el estado del match")
    
    coincide_capacidad = models.BooleanField(default=False)
    coincide_mascotas = models.BooleanField(default=False)
    porcentaje_compatibilidad = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Match'
        verbose_name_plural = 'Matches'
        unique_together = ['huesped', 'afectado']
    
    def __str__(self):
        return f"{self.huesped.nombres} ↔ {self.afectado.nombres} ({self.get_estado_display()})"
    
    def calcular_porcentaje(self):
        """Calcula el porcentaje de compatibilidad entre huésped y afectado"""
        puntos = 0
        total = 2  # Capacidad + Mascotas
        
        # 1. Capacidad: huésped debe tener capacidad suficiente para el núcleo familiar
        if self.huesped.cantidad_personas >= self.afectado.cantidad_total():
            puntos += 1
            self.coincide_capacidad = True
        
        # 2. Mascotas: coincidencia en mascotas
        if self.huesped.acepta_mascotas == self.afectado.tiene_mascotas:
            puntos += 1
            self.coincide_mascotas = True
        elif self.huesped.acepta_mascotas and not self.afectado.tiene_mascotas:
            puntos += 1
            self.coincide_mascotas = True
        
        self.porcentaje_compatibilidad = int((puntos / total) * 100)
        return self.porcentaje_compatibilidad