from django.contrib import admin
from .models import Huesped, Afectado

@admin.register(Huesped)
class HuespedAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombres', 'apellidos', 'cedula_completa', 'ciudad', 'estado', 'tipo_acogida')
    search_fields = ('nombres', 'apellidos', 'numero_cedula', 'ciudad', 'estado')
    list_filter = ('estado', 'tipo_acogida', 'estado_verificacion')

admin.site.register(Afectado)