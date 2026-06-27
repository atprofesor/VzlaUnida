from django import forms
from .models import Huesped

class HuespedRegistrationForm(forms.ModelForm):
    class Meta:
        model = Huesped
        # Definimos qué campos aparecerán en el formulario
        fields = [
            'telefono', 'ciudad', 'estado', 'sector', 
            'capacidad_ninos', 'capacidad_adultos', 'capacidad_adultos_mayores',
            'acepta_mascotas_pequenas', 'acepta_mascotas_medianas', 'acepta_mascotas_grandes',
            'tipo_acogida', 'tiempo_disponible_meses', 'cedula_file', 'residencia_file'
        ]
        # Opcional: Añadir clases de CSS (estilo Tailwind) a cada campo
        widgets = {
            'telefono': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg'}),
            'ciudad': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg'}),
            # ... puedes ir añadiendo clases a los demás para que se vean bien
        }