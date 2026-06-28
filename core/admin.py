from django.contrib import admin
from .models import Huesped, Afectado

@admin.register(Huesped)
class HuespedAdmin(admin.ModelAdmin):
    list_display = ('id', 'ciudad', 'estado', 'tipo_acogida') # Para verlo ordenado
    search_fields = ('ciudad', 'estado')

admin.site.register(Afectado)