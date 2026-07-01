from django.contrib import admin
from django.urls import reverse
from django.utils.html import mark_safe
from django.utils import timezone
from django.contrib import messages
from .models import Huesped, Afectado, ESTADO_VERIFICACION_CHOICES

@admin.register(Huesped)
class HuespedAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'nombres', 
        'apellidos', 
        'cedula_completa', 
        'telefono',
        'ciudad', 
        'estado', 
        'tipo_acogida',
        'verificacion_con_estilo',
        'fecha_verificacion_display',
        'has_email',
        'acciones_verificacion'
    )
    
    search_fields = (
        'nombres', 
        'apellidos', 
        'numero_cedula', 
        'telefono',
        'ciudad', 
        'estado',
        'sector'
    )
    
    list_filter = (
        'estado', 
        'ciudad',
        'tipo_acogida', 
        'estado_verificacion',
        'fecha_verificacion',
        'prefijo_cedula',
    )
    
    ordering = ('-id',)
    
    readonly_fields = (
        'user',
        'fecha_verificacion',
        'ver_documentos',
        'verificacion_con_estilo',
    )
    
    fieldsets = (
        ('Información Personal', {
            'fields': (
                'user',
                'nombres', 
                'apellidos',
                ('prefijo_cedula', 'numero_cedula'),
                'telefono',
            )
        }),
        ('Ubicación', {
            'fields': (
                ('estado', 'ciudad'),
                'sector',
            )
        }),
        ('Capacidad de Acogida', {
            'fields': (
                ('capacidad_ninos', 'capacidad_adultos', 'capacidad_adultos_mayores'),
                'tipo_acogida',
                'tiempo_disponible_meses',
            )
        }),
        ('Mascotas', {
            'fields': (
                ('acepta_mascotas_pequenas', 'acepta_mascotas_medianas', 'acepta_mascotas_grandes'),
            )
        }),
        ('Documentación', {
            'fields': (
                'cedula_file',
                'residencia_file',
                'ver_documentos',
            )
        }),
        ('Verificación', {
            'fields': (
                'estado_verificacion',
                'comentario_verificacion',
                'fecha_verificacion',
                'verificacion_con_estilo',
            )
        }),
    )
    
    actions = ['aprobar_huéspedes', 'rechazar_huéspedes', 'marcar_en_revision']
    
    def has_email(self, obj):
        if obj.user and obj.user.email:
            return mark_safe(f'<span style="color:#16A34A;">✅ {obj.user.email}</span>')
        return mark_safe('<span style="color:#DC2626;">❌ Sin email</span>')
    has_email.short_description = 'Email'
    
    def verificacion_con_estilo(self, obj):
        colores = {
            'pendiente': 'background-color:#FEF3C7;color:#92400E;',
            'en_revision': 'background-color:#DBEAFE;color:#1E40AF;',
            'aprobado': 'background-color:#D1FAE5;color:#065F46;',
            'rechazado': 'background-color:#FEE2E2;color:#991B1B;',
            'requiere_correccion': 'background-color:#FFEDD5;color:#9A3412;',
        }
        emojis = {
            'pendiente': '⏳',
            'en_revision': '🔍',
            'aprobado': '✅',
            'rechazado': '❌',
            'requiere_correccion': '📝',
        }
        
        estado = obj.estado_verificacion
        color = colores.get(estado, 'background-color:#F3F4F6;color:#374151;')
        emoji = emojis.get(estado, '')
        texto = dict(ESTADO_VERIFICACION_CHOICES).get(estado, estado)
        
        return mark_safe(
            f'<span style="display:inline-block;padding:4px 12px;border-radius:9999px;font-size:13px;font-weight:700;{color}">{emoji} {texto}</span>'
        )
    verificacion_con_estilo.short_description = 'Estado'
    verificacion_con_estilo.admin_order_field = 'estado_verificacion'
    
    def fecha_verificacion_display(self, obj):
        if obj.fecha_verificacion:
            return obj.fecha_verificacion.strftime('%d/%m/%Y %H:%M')
        return '-'
    fecha_verificacion_display.short_description = 'Fecha Verif.'
    fecha_verificacion_display.admin_order_field = 'fecha_verificacion'
    
    def ver_documentos(self, obj):
        links = []
        
        if obj.cedula_file:
            links.append(
                f'<a href="{obj.cedula_file.url}" target="_blank" style="background:#4F46E5;color:white;padding:2px 10px;border-radius:4px;text-decoration:none;display:inline-block;margin:2px 0;">📄 Ver Cédula</a>'
            )
        else:
            links.append('<span style="color:#DC2626;">❌ Sin cédula</span>')
            
        if obj.residencia_file:
            links.append(
                f'<a href="{obj.residencia_file.url}" target="_blank" style="background:#4F46E5;color:white;padding:2px 10px;border-radius:4px;text-decoration:none;display:inline-block;margin:2px 0;">📄 Ver Residencia</a>'
            )
        else:
            links.append('<span style="color:#DC2626;">❌ Sin residencia</span>')
            
        return mark_safe('<br>'.join(links))
    ver_documentos.short_description = 'Documentos'
    
    def acciones_verificacion(self, obj):
        if obj.estado_verificacion not in ['aprobado', 'rechazado']:
            aprobar_url = reverse('admin:aprobar_huesped_direct', args=[obj.id])
            rechazar_url = reverse('admin:rechazar_huesped_direct', args=[obj.id])
            corregir_url = reverse('admin:solicitar_correccion_huesped_direct', args=[obj.id])
            revision_url = reverse('admin:marcar_en_revision_huesped_direct', args=[obj.id])
            
            return mark_safe(
                f'''
                <div style="display:flex;gap:4px;flex-wrap:wrap;">
                    <a href="{aprobar_url}" style="background:#16A34A;color:white;padding:2px 8px;border-radius:4px;text-decoration:none;font-size:11px;display:inline-block;">✅ Aprobar</a>
                    <a href="{rechazar_url}" style="background:#DC2626;color:white;padding:2px 8px;border-radius:4px;text-decoration:none;font-size:11px;display:inline-block;">❌ Rechazar</a>
                    <a href="{corregir_url}" style="background:#EA580C;color:white;padding:2px 8px;border-radius:4px;text-decoration:none;font-size:11px;display:inline-block;">📝 Corregir</a>
                    <a href="{revision_url}" style="background:#2563EB;color:white;padding:2px 8px;border-radius:4px;text-decoration:none;font-size:11px;display:inline-block;">🔍 Revisar</a>
                </div>
                '''
            )
        return mark_safe('<span style="color:#6B7280;font-size:12px;">✓ Completado</span>')
    acciones_verificacion.short_description = 'Acciones'
    
    def aprobar_huéspedes(self, request, queryset):
        count = 0
        for huesped in queryset:
            if huesped.estado_verificacion != 'aprobado':
                huesped.estado_verificacion = 'aprobado'
                huesped.fecha_verificacion = timezone.now()
                huesped.save()
                count += 1
        self.message_user(request, f'✅ {count} huéspedes aprobados correctamente.')
    aprobar_huéspedes.short_description = '✅ Aprobar huéspedes seleccionados'
    
    def rechazar_huéspedes(self, request, queryset):
        count = 0
        for huesped in queryset:
            if huesped.estado_verificacion != 'rechazado':
                huesped.estado_verificacion = 'rechazado'
                huesped.fecha_verificacion = timezone.now()
                huesped.save()
                count += 1
        self.message_user(request, f'❌ {count} huéspedes rechazados.')
    rechazar_huéspedes.short_description = '❌ Rechazar huéspedes seleccionados'
    
    def marcar_en_revision(self, request, queryset):
        count = 0
        for huesped in queryset:
            if huesped.estado_verificacion == 'pendiente':
                huesped.estado_verificacion = 'en_revision'
                huesped.save()
                count += 1
        self.message_user(request, f'🔍 {count} huéspedes marcados como "En Revisión".')
    marcar_en_revision.short_description = '🔍 Marcar como "En Revisión"'
    
    def save_model(self, request, obj, form, change):
        if change:
            original = Huesped.objects.get(pk=obj.pk)
            if original.estado_verificacion != obj.estado_verificacion:
                if obj.estado_verificacion in ['aprobado', 'rechazado']:
                    obj.fecha_verificacion = timezone.now()
                elif obj.estado_verificacion == 'pendiente':
                    obj.fecha_verificacion = None
        
        super().save_model(request, obj, form, change)
    
    def get_urls(self):
        from django.urls import path
        from django.http import HttpResponseRedirect
        from django.shortcuts import get_object_or_404
        
        def aprobar_huesped_direct(request, pk):
            huesped = get_object_or_404(Huesped, pk=pk)
            if huesped.estado_verificacion != 'aprobado':
                huesped.estado_verificacion = 'aprobado'
                huesped.fecha_verificacion = timezone.now()
                huesped.comentario_verificacion = 'Aprobado por administrador.'
                huesped.save()
                messages.success(request, f'✅ Huésped {huesped.nombres} {huesped.apellidos} aprobado.')
            return HttpResponseRedirect(reverse('admin:core_huesped_changelist'))
        
        def rechazar_huesped_direct(request, pk):
            huesped = get_object_or_404(Huesped, pk=pk)
            if huesped.estado_verificacion != 'rechazado':
                huesped.estado_verificacion = 'rechazado'
                huesped.fecha_verificacion = timezone.now()
                huesped.comentario_verificacion = 'Rechazado por administrador.'
                huesped.save()
                messages.warning(request, f'❌ Huésped {huesped.nombres} {huesped.apellidos} rechazado.')
            return HttpResponseRedirect(reverse('admin:core_huesped_changelist'))
        
        def solicitar_correccion_huesped_direct(request, pk):
            huesped = get_object_or_404(Huesped, pk=pk)
            huesped.estado_verificacion = 'requiere_correccion'
            huesped.comentario_verificacion = 'Se requieren correcciones. Por favor contacta al administrador.'
            huesped.save()
            messages.info(request, f'📝 Se ha solicitado corrección para {huesped.nombres} {huesped.apellidos}.')
            return HttpResponseRedirect(reverse('admin:core_huesped_changelist'))
        
        def marcar_en_revision_huesped_direct(request, pk):
            huesped = get_object_or_404(Huesped, pk=pk)
            huesped.estado_verificacion = 'en_revision'
            huesped.save()
            messages.info(request, f'🔍 Huésped {huesped.nombres} {huesped.apellidos} marcado como "En Revisión".')
            return HttpResponseRedirect(reverse('admin:core_huesped_changelist'))
        
        custom_urls = [
            path('aprobar/<int:pk>/', self.admin_site.admin_view(aprobar_huesped_direct), name='aprobar_huesped_direct'),
            path('rechazar/<int:pk>/', self.admin_site.admin_view(rechazar_huesped_direct), name='rechazar_huesped_direct'),
            path('corregir/<int:pk>/', self.admin_site.admin_view(solicitar_correccion_huesped_direct), name='solicitar_correccion_huesped_direct'),
            path('revision/<int:pk>/', self.admin_site.admin_view(marcar_en_revision_huesped_direct), name='marcar_en_revision_huesped_direct'),
        ]
        return custom_urls + super().get_urls()


@admin.register(Afectado)
class AfectadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_completo', 'telefono', 'ciudad', 'estado')
    search_fields = ('nombre_completo', 'telefono', 'ciudad', 'estado')
    list_filter = ('estado', 'ciudad')
    ordering = ('-id',)