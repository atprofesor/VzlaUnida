from django import forms
from django.contrib.auth.models import User
from .models import Huesped, UBICACIONES, TIPO_ACOGIDA_CHOICES
import os
import re

class RegistroUsuarioForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}))
    
    class Meta:
        model = User
        fields = ['username', 'password']
        widgets = {'username': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'})}

class HuespedRegistrationForm(forms.ModelForm):
    # CÉDULA CON PREFIJO - SOLO "V" Y "E"
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
    
    # ✅ CAMBIADO: De ChoiceField a CharField para evitar validación
    ciudad = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border rounded-lg bg-slate-50',
            'id': 'id_ciudad',
            'readonly': 'readonly',  # ✅ Hace que sea solo lectura
            'placeholder': 'Selecciona un estado primero'
        })
    )

    class Meta:
        model = Huesped
        exclude = ['user', 'estado_verificacion', 'telefono', 'ciudad', 'estado', 'prefijo_cedula', 'numero_cedula']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
            'apellidos': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
            'sector': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
            'capacidad_ninos': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
            'capacidad_adultos': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
            'capacidad_adultos_mayores': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
            'tipo_acogida': forms.Select(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
            'tiempo_disponible_meses': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg bg-slate-50'}),
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