from django import forms
from .models import Huesped, UBICACIONES, TIPO_ACOGIDA_CHOICES

TELEFONO_CHOICES = [('0412', '0412'), ('0422', '0422'), ('0414', '0414'), ('0424', '0424'), ('0416', '0416'), ('0426', '0426')]

class HuespedRegistrationForm(forms.ModelForm):
    # Campos manuales con fondo gris (bg-slate-50)
    prefijo_telefono = forms.ChoiceField(choices=TELEFONO_CHOICES, widget=forms.Select(attrs={'class': 'p-2 border rounded-lg bg-slate-50'}))
    numero_telefono = forms.CharField(max_length=7, min_length=7, widget=forms.TextInput(attrs={'class': 'p-2 border rounded-lg bg-slate-50', 'placeholder': '1234567'}))
    
    estado = forms.ChoiceField(choices=[('', 'Seleccione Estado')] + [(e, e) for e in UBICACIONES.keys()], widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}))
    ciudad = forms.ChoiceField(choices=[('', 'Seleccione Ciudad')], widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}))

    tipo_acogida = forms.ChoiceField(
        choices=TIPO_ACOGIDA_CHOICES, 
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'})
    )

    # Campos automáticos personalizados con el widget para aplicar el estilo gris
    sector = forms.CharField(
            label="Dirección / Sector", 
            widget=forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-lg bg-slate-50',
                'placeholder': 'Ej: Calle Principal, Sector La Esperanza'
            })
    )
    
    capacidad_ninos = forms.IntegerField(
        label="Niños", 
        widget=forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'})
    )
    capacidad_adultos = forms.IntegerField(
        label="Adultos", 
        widget=forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'})
    )
    capacidad_adultos_mayores = forms.IntegerField(
        label="Adultos mayores", 
        widget=forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'})
    )
 
    tiempo_disponible_meses = forms.IntegerField(
        label="Meses disponibles",
        widget=forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'})
    )

    class Meta:
        model = Huesped
        fields = [
            'sector', 'capacidad_ninos', 'capacidad_adultos', 
            'capacidad_adultos_mayores', 'acepta_mascotas_pequenas', 
            'acepta_mascotas_medianas', 'acepta_mascotas_grandes', 
            'tipo_acogida', 'tiempo_disponible_meses', 'cedula_file', 'residencia_file'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si se recibe un POST, reconstruimos las opciones de ciudad para validar correctamente
        if 'estado' in self.data:
            try:
                estado_seleccionado = self.data.get('estado')
                ciudades = UBICACIONES.get(estado_seleccionado, [])
                self.fields['ciudad'].choices = [('', 'Seleccione Ciudad')] + [(c, c) for c in ciudades]
            except (ValueError, TypeError):
                pass

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.telefono = f"{self.cleaned_data['prefijo_telefono']}{self.cleaned_data['numero_telefono']}"
        instance.estado = self.cleaned_data['estado']
        instance.ciudad = self.cleaned_data['ciudad']
        if commit:
            instance.save()
        return instance