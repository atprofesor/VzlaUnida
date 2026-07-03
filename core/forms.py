from django import forms
from django.contrib.auth.models import User
from .models import Huesped, UBICACIONES, TIPO_ACOGIDA_CHOICES
import os

class RegistroUsuarioForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full p-2 border rounded-lg bg-slate-50',
            'placeholder': 'tu@email.com'
        }),
        required=True,
        help_text="Obligatorio para recibir notificaciones de verificación"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email


class HuespedRegistrationForm(forms.ModelForm):
    # CÉDULA CON PREFIJO
    prefijo_cedula = forms.ChoiceField(
        choices=[('V', 'V'), ('E', 'E')],
        widget=forms.Select(attrs={'class': 'p-2 border rounded-lg bg-slate-50'})
    )
    numero_cedula = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'p-2 border rounded-lg bg-slate-50',
            'placeholder': '17.936.063',
            'id': 'id_numero_cedula'
        })
    )
    
    prefijo_telefono = forms.ChoiceField(
        choices=[('0412','0412'),('0422','0422'),('0414','0414'),('0424','0424'),('0416','0416'),('0426','0426')], 
        widget=forms.Select(attrs={'class': 'p-2 border rounded-lg bg-slate-50'})
    )
    numero_telefono = forms.CharField(
        max_length=7, 
        widget=forms.TextInput(attrs={'class': 'p-2 border rounded-lg bg-slate-50'})
    )
    
    estado = forms.ChoiceField(
        choices=[('', 'Seleccione Estado')] + [(e, e) for e in UBICACIONES.keys()], 
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'})
    )
    
    ciudad = forms.ChoiceField(
        choices=[('', 'Seleccione Ciudad')],
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'})
    )

    # ✅ CANTIDAD DE PERSONAS (ChoiceField 1-9)
    cantidad_personas = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 10)],
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'})
    )

    # ✅ MASCOTAS - Simplificado a un solo checkbox
    acepta_mascotas = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-primary rounded border-gray-300 focus:ring-primary'})
    )

    # CAMPO MESES COMO LISTA DESPLEGABLE
    tiempo_disponible_meses = forms.ChoiceField(
        choices=[(1, '1 mes'), (3, '3 meses'), (6, '6 meses'), (9, '9 meses'), (12, '12 meses')],
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'})
    )

    class Meta:
        model = Huesped
        exclude = [
            'user', 'estado_verificacion', 'telefono', 'ciudad', 'estado', 
            'prefijo_cedula', 'numero_cedula', 'capacidad_ninos', 'capacidad_adultos', 
            'capacidad_adultos_mayores', 'acepta_mascotas_pequenas', 
            'acepta_mascotas_medianas', 'acepta_mascotas_grandes'
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
            'apellidos': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
            'sector': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
            'tipo_acogida': forms.Select(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
        }

    # ✅ VALIDACIÓN DE CÉDULA
    def clean_numero_cedula(self):
        numero = self.cleaned_data.get('numero_cedula', '')
        numero_limpio = numero.replace('.', '')
        
        if not numero_limpio.isdigit():
            raise forms.ValidationError("La cédula debe contener solo números (ej: 17936063)")
        
        if len(numero_limpio) < 6 or len(numero_limpio) > 8:
            raise forms.ValidationError("La cédula debe tener entre 6 y 8 dígitos")
        
        if len(numero_limpio) == 8:
            formateado = f"{numero_limpio[:2]}.{numero_limpio[2:5]}.{numero_limpio[5:]}"
        elif len(numero_limpio) == 7:
            formateado = f"{numero_limpio[:1]}.{numero_limpio[1:4]}.{numero_limpio[4:]}"
        else:
            formateado = numero_limpio
        
        return formateado

    # ✅ VALIDACIÓN DE CÉDULA ÚNICA
    def clean(self):
        cleaned_data = super().clean()
        prefijo = cleaned_data.get('prefijo_cedula')
        numero = cleaned_data.get('numero_cedula')
        
        # Verificar si ya existe un huésped con esta cédula
        if prefijo and numero:
            numero_limpio = numero.replace('.', '')
            
            existe = Huesped.objects.filter(
                prefijo_cedula=prefijo,
                numero_cedula=numero_limpio
            ).exists()
            
            if not existe:
                existe = Huesped.objects.filter(
                    prefijo_cedula=prefijo,
                    numero_cedula=numero
                ).exists()
            
            if existe:
                self.add_error(
                    'numero_cedula',
                    f"Ya existe un huésped registrado con la cédula {prefijo}-{numero}. "
                    "Si eres tú, inicia sesión en tu cuenta."
                )
                return cleaned_data
        
        # ✅ VALIDACIÓN DE CANTIDAD DE PERSONAS
        cantidad_personas = cleaned_data.get('cantidad_personas')
        if cantidad_personas:
            try:
                cantidad = int(cantidad_personas)
                if cantidad < 1 or cantidad > 9:
                    self.add_error(
                        'cantidad_personas',
                        "La cantidad de personas debe estar entre 1 y 9."
                    )
            except (ValueError, TypeError):
                self.add_error(
                    'cantidad_personas',
                    "Selecciona una cantidad válida."
                )
        
        # Validación de ciudad
        estado = cleaned_data.get('estado')
        ciudad = cleaned_data.get('ciudad')
        
        if estado and ciudad:
            if estado not in UBICACIONES:
                self.add_error('estado', "Estado no válido.")
                return cleaned_data
            if ciudad not in UBICACIONES.get(estado, []):
                self.add_error(
                    'ciudad',
                    f"La ciudad '{ciudad}' no pertenece al estado '{estado}'. "
                    f"Ciudades disponibles: {', '.join(UBICACIONES.get(estado, []))}"
                )
        
        return cleaned_data

    # ✅ VALIDACIÓN DE ARCHIVO CÉDULA
    def clean_cedula_file(self):
        file = self.cleaned_data.get('cedula_file')
        if not file:
            raise forms.ValidationError("El archivo de cédula es obligatorio.")
        
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.pdf']:
            raise forms.ValidationError("Solo se permiten archivos JPG, PNG o PDF.")
        
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("El archivo no debe superar los 5MB.")
        
        return file

    # ✅ VALIDACIÓN DE ARCHIVO RESIDENCIA
    def clean_residencia_file(self):
        file = self.cleaned_data.get('residencia_file')
        if not file:
            raise forms.ValidationError("El comprobante de residencia es obligatorio.")
        
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.pdf']:
            raise forms.ValidationError("Solo se permiten archivos JPG, PNG o PDF.")
        
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("El archivo no debe superar los 5MB.")
        
        return file

    # ✅ INICIALIZAR EL FORMULARIO PARA ACTUALIZAR CHOICES DE CIUDAD
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si hay un estado seleccionado, actualizar las opciones de ciudad
        estado_seleccionado = self.initial.get('estado') or self.data.get('estado')
        if estado_seleccionado and estado_seleccionado in UBICACIONES:
            ciudades = UBICACIONES[estado_seleccionado]
            self.fields['ciudad'].choices = [('', 'Seleccione Ciudad')] + [(c, c) for c in ciudades]