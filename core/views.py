import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from .models import Huesped, Afectado, UBICACIONES, ESTADO_VERIFICACION_CHOICES
from .forms import RegistroUsuarioForm, HuespedRegistrationForm

# ✅ FUNCIÓN DE VERIFICACIÓN PARA ADMINISTRADORES
def es_administrador(user):
    """Verifica si el usuario es administrador (staff o superuser)"""
    return user.is_authenticated and user.is_staff

# ✅ FUNCIÓN PARA ENVIAR NOTIFICACIONES POR EMAIL
def enviar_notificacion_verificacion(huesped, estado_anterior=None):
    """
    Envía un correo electrónico al huésped notificando el cambio en su estado de verificación.
    """
    if not huesped.user or not huesped.user.email:
        return
    
    mensajes = {
        'aprobado': {
            'asunto': '✅ ¡Tu perfil ha sido aprobado!',
            'mensaje': f"""
Hola {huesped.nombres},

¡Excelentes noticias! Tu perfil como huésped en VzlaUnida ha sido APROBADO.

Ya puedes:
- ✅ Ver afectados cercanos en tu área
- ✅ Recibir solicitudes de alojamiento
- ✅ Conectar con personas que necesitan ayuda

Tu capacidad de alojamiento: {huesped.capacidad_total()} personas
Ubicación: {huesped.ciudad}, {huesped.estado}

Gracias por formar parte de esta red de apoyo.

Saludos,
El equipo de VzlaUnida
"""
        },
        'rechazado': {
            'asunto': '❌ Tu perfil ha sido rechazado',
            'mensaje': f"""
Hola {huesped.nombres},

Lamentamos informarte que tu perfil como huésped en VzlaUnida ha sido RECHAZADO.

Motivo: {huesped.comentario_verificacion or 'No se especificó motivo.'}

¿Qué puedes hacer?
1. Revisa los documentos que subiste (cédula y residencia)
2. Asegúrate de que sean legibles y estén actualizados
3. Vuelve a registrarte con la información correcta

Si crees que esto es un error, por favor contacta a nuestro equipo de soporte.

Saludos,
El equipo de VzlaUnida
"""
        },
        'requiere_correccion': {
            'asunto': '📝 Tu perfil requiere correcciones',
            'mensaje': f"""
Hola {huesped.nombres},

Tu perfil como huésped en VzlaUnida requiere algunas correcciones.

Comentario del administrador:
{huesped.comentario_verificacion}

Por favor, inicia sesión en tu cuenta y actualiza la información según lo indicado.

Saludos,
El equipo de VzlaUnida
"""
        },
        'en_revision': {
            'asunto': '🔍 Tu perfil está en revisión',
            'mensaje': f"""
Hola {huesped.nombres},

Te informamos que tu perfil como huésped en VzlaUnida está siendo revisado por nuestro equipo.

Este proceso puede tomar hasta 48 horas. Te notificaremos cuando tengamos una respuesta.

Gracias por tu paciencia.

Saludos,
El equipo de VzlaUnida
"""
        }
    }
    
    info = mensajes.get(huesped.estado_verificacion)
    if not info:
        return
    
    try:
        send_mail(
            subject=info['asunto'],
            message=info['mensaje'],
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[huesped.user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error al enviar notificación a {huesped.user.email}: {e}")


@transaction.atomic
def registrar_huesped(request):
    """
    Vista para registrar un nuevo huésped.
    Crea usuario y perfil de huésped en una transacción atómica.
    """
    # ✅ SI EL USUARIO YA ESTÁ AUTENTICADO, REDIRIGIR AL DASHBOARD
    if request.user.is_authenticated:
        try:
            huesped = Huesped.objects.get(user=request.user)
            messages.info(request, 'Ya tienes un perfil de huésped registrado.')
            return redirect('dashboard_huesped')
        except Huesped.DoesNotExist:
            messages.warning(request, 'Ya has iniciado sesión. Si quieres registrar un huésped, contacta al administrador.')
            return redirect('home')
    
    if request.method == 'POST':
        user_form = RegistroUsuarioForm(request.POST)
        huesped_form = HuespedRegistrationForm(request.POST, request.FILES)
        
        if user_form.is_valid() and huesped_form.is_valid():
            try:
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data['password'])
                user.email = user_form.cleaned_data['email']
                user.save()
                
                huesped = huesped_form.save(commit=False)
                huesped.user = user
                huesped.telefono = f"{huesped_form.cleaned_data['prefijo_telefono']}{huesped_form.cleaned_data['numero_telefono']}"
                huesped.estado = huesped_form.cleaned_data['estado']
                huesped.ciudad = huesped_form.cleaned_data['ciudad']
                huesped.tiempo_disponible_meses = int(huesped_form.cleaned_data['tiempo_disponible_meses'])
                
                huesped.prefijo_cedula = huesped_form.cleaned_data['prefijo_cedula']
                huesped.numero_cedula = huesped_form.cleaned_data['numero_cedula']
                
                huesped.estado_verificacion = 'pendiente'
                
                huesped.save()
                
                if user.email:
                    try:
                        send_mail(
                            subject='✅ Registro exitoso en VzlaUnida',
                            message=f"""
Hola {huesped.nombres},

¡Bienvenido a VzlaUnida! Tu registro como huésped ha sido exitoso.

📋 Estado actual: Pendiente de verificación
⏳ Tiempo estimado: 24-48 horas

Una vez que nuestro equipo verifique tus documentos, recibirás una notificación.

Gracias por ser parte de esta red de apoyo.

Saludos,
El equipo de VzlaUnida
""",
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[user.email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        print(f"Error al enviar correo de bienvenida: {e}")
                
                login(request, user)
                
                messages.success(
                    request, 
                    f'¡Bienvenido {huesped.nombres}! Tu registro fue exitoso. '
                    'Te hemos enviado un correo de confirmación. '
                    'Tu perfil está pendiente de verificación.'
                )
                
                return redirect('dashboard_huesped')
                
            except Exception as e:
                if 'user' in locals():
                    user.delete()
                messages.error(request, f'Ocurrió un error: {str(e)}')
                return render(request, 'registro_huesped.html', {
                    'user_form': user_form,
                    'huesped_form': huesped_form,
                    'ubicaciones_json': json.dumps(UBICACIONES)
                })
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
            return render(request, 'registro_huesped.html', {
                'user_form': user_form,
                'huesped_form': huesped_form,
                'ubicaciones_json': json.dumps(UBICACIONES)
            })
    
    else:
        user_form = RegistroUsuarioForm()
        huesped_form = HuespedRegistrationForm()
    
    return render(request, 'registro_huesped.html', {
        'user_form': user_form,
        'huesped_form': huesped_form,
        'ubicaciones_json': json.dumps(UBICACIONES)
    })


def home_seleccion(request):
    """
    Página de inicio con selección de tipo de usuario.
    Si el usuario ya está autenticado, redirigir al dashboard.
    """
    # ✅ SI EL USUARIO YA ESTÁ AUTENTICADO, REDIRIGIR AL DASHBOARD
    if request.user.is_authenticated:
        try:
            # Verificar si tiene perfil de huésped
            huesped = Huesped.objects.get(user=request.user)
            messages.info(request, 'Ya has iniciado sesión.')
            return redirect('dashboard_huesped')
        except Huesped.DoesNotExist:
            # Si está autenticado pero no tiene perfil de huésped (admin)
            messages.info(request, 'Ya has iniciado sesión como administrador.')
            return redirect('home')  # O a donde quieras redirigir a los admins
    
    return render(request, 'home.html')


@login_required
def dashboard_huesped(request):
    try:
        huesped = Huesped.objects.get(user=request.user)
        
        estado_info = {
            'clase': '',
            'icono': '',
            'mensaje': '',
            'color': ''
        }
        
        if huesped.estado_verificacion == 'aprobado':
            estado_info = {
                'clase': 'bg-green-100 text-green-800 border-green-300',
                'icono': '✅',
                'mensaje': '¡Tu perfil ha sido verificado! Ya puedes recibir afectados.',
                'color': 'verde'
            }
        elif huesped.estado_verificacion == 'rechazado':
            estado_info = {
                'clase': 'bg-red-100 text-red-800 border-red-300',
                'icono': '❌',
                'mensaje': 'Tu perfil ha sido rechazado. Por favor contacta al administrador.',
                'color': 'rojo'
            }
        elif huesped.estado_verificacion == 'en_revision':
            estado_info = {
                'clase': 'bg-blue-100 text-blue-800 border-blue-300',
                'icono': '🔍',
                'mensaje': 'Tu perfil está siendo revisado por el administrador. Pronto recibirás respuesta.',
                'color': 'azul'
            }
        elif huesped.estado_verificacion == 'requiere_correccion':
            estado_info = {
                'clase': 'bg-orange-100 text-orange-800 border-orange-300',
                'icono': '📝',
                'mensaje': f'Tu perfil requiere correcciones: {huesped.comentario_verificacion or "Por favor revisa los documentos."}',
                'color': 'naranja'
            }
        else:
            estado_info = {
                'clase': 'bg-yellow-100 text-yellow-800 border-yellow-300',
                'icono': '⏳',
                'mensaje': 'Tu perfil está pendiente de verificación. El administrador revisará tus documentos.',
                'color': 'amarillo'
            }
        
        afectados_cercanos = []
        if huesped.estado_verificacion == 'aprobado':
            try:
                afectados_cercanos = Afectado.objects.filter(
                    models.Q(ciudad=huesped.ciudad) | models.Q(estado=huesped.estado)
                ).order_by('-id')[:10]
            except:
                afectados_cercanos = []
        
        try:
            total_afectados_estado = Afectado.objects.filter(
                estado=huesped.estado
            ).count()
            total_afectados_ciudad = Afectado.objects.filter(
                ciudad=huesped.ciudad
            ).count()
        except:
            total_afectados_estado = 0
            total_afectados_ciudad = 0
        
        otros_huespedes = Huesped.objects.filter(
            estado=huesped.estado,
            estado_verificacion='aprobado'
        ).exclude(id=huesped.id)[:5]
        
        capacidad_total = (
            huesped.capacidad_ninos + 
            huesped.capacidad_adultos + 
            huesped.capacidad_adultos_mayores
        )
        
        top_huespedes = Huesped.objects.filter(
            estado=huesped.estado,
            estado_verificacion='aprobado'
        ).exclude(id=huesped.id).order_by(
            '-capacidad_ninos', 
            '-capacidad_adultos', 
            '-capacidad_adultos_mayores'
        )[:3]
        
        context = {
            'huesped': huesped,
            'afectados_cercanos': afectados_cercanos,
            'otros_huespedes': otros_huespedes,
            'top_huespedes': top_huespedes,
            'capacidad_total': capacidad_total,
            'total_afectados_estado': total_afectados_estado,
            'total_afectados_ciudad': total_afectados_ciudad,
            'mensaje_bienvenida': f'¡Bienvenido, {huesped.nombres}!',
            'estado_info': estado_info,
        }
        
        return render(request, 'dashboard_huesped.html', context)
        
    except Huesped.DoesNotExist:
        messages.warning(request, 'No tienes un perfil de huésped completo.')
        return redirect('registrar_huesped')
    except Exception as e:
        messages.error(request, f'Error al cargar el dashboard: {str(e)}')
        return redirect('home')


@login_required
def perfil_huesped(request):
    try:
        huesped = Huesped.objects.get(user=request.user)
        
        if request.method == 'POST':
            pass
        
        context = {
            'huesped': huesped,
            'capacidad_total': (
                huesped.capacidad_ninos + 
                huesped.capacidad_adultos + 
                huesped.capacidad_adultos_mayores
            )
        }
        return render(request, 'perfil_huesped.html', context)
        
    except Huesped.DoesNotExist:
        messages.warning(request, 'No tienes un perfil de huésped.')
        return redirect('registrar_huesped')


@login_required
def buscar_afectados(request):
    try:
        huesped = Huesped.objects.get(user=request.user)
        
        if huesped.estado_verificacion != 'aprobado':
            messages.warning(
                request, 
                'Tu perfil debe estar verificado para buscar afectados. '
                'Estado actual: ' + dict(ESTADO_VERIFICACION_CHOICES).get(huesped.estado_verificacion, huesped.estado_verificacion)
            )
            return redirect('dashboard_huesped')
        
        estado = request.GET.get('estado', '')
        ciudad = request.GET.get('ciudad', '')
        capacidad_minima = request.GET.get('capacidad_minima', 0)
        
        try:
            afectados = Afectado.objects.all()
            
            if estado:
                afectados = afectados.filter(estado=estado)
            if ciudad:
                afectados = afectados.filter(ciudad=ciudad)
            
            afectados = afectados.order_by('-id')
        except:
            afectados = []
        
        context = {
            'huesped': huesped,
            'afectados': afectados,
            'filtros': {
                'estado': estado,
                'ciudad': ciudad,
                'capacidad_minima': capacidad_minima,
            }
        }
        return render(request, 'buscar_afectados.html', context)
        
    except Huesped.DoesNotExist:
        messages.warning(request, 'No tienes un perfil de huésped.')
        return redirect('registrar_huesped')


def login_view(request):
    if request.user.is_authenticated:
        try:
            Huesped.objects.get(user=request.user)
            return redirect('dashboard_huesped')
        except Huesped.DoesNotExist:
            return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            try:
                huesped = Huesped.objects.get(user=user)
                messages.success(request, f'¡Bienvenido de vuelta, {huesped.nombres}!')
                return redirect('dashboard_huesped')
            except Huesped.DoesNotExist:
                messages.success(request, f'¡Bienvenido, {user.username}!')
                return redirect('home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('home')


# ✅ VISTAS DE VALIDACIÓN
@login_required
@user_passes_test(es_administrador)
def aprobar_huesped(request, pk):
    if request.method == 'POST':
        huesped = get_object_or_404(Huesped, pk=pk)
        estado_anterior = huesped.estado_verificacion
        
        huesped.estado_verificacion = 'aprobado'
        huesped.fecha_verificacion = timezone.now()
        huesped.comentario_verificacion = request.POST.get('comentario', 'Aprobado por administrador.')
        huesped.save()
        
        enviar_notificacion_verificacion(huesped, estado_anterior)
        
        messages.success(request, f'✅ Huésped {huesped.nombres} {huesped.apellidos} aprobado. '
                                f'Notificación enviada a {huesped.user.email or "sin email registrado"}')
        return redirect('admin:core_huesped_changelist')
    
    return redirect('admin:core_huesped_changelist')


@login_required
@user_passes_test(es_administrador)
def rechazar_huesped(request, pk):
    if request.method == 'POST':
        huesped = get_object_or_404(Huesped, pk=pk)
        estado_anterior = huesped.estado_verificacion
        
        huesped.estado_verificacion = 'rechazado'
        huesped.fecha_verificacion = timezone.now()
        huesped.comentario_verificacion = request.POST.get('comentario', 'Rechazado por administrador.')
        huesped.save()
        
        enviar_notificacion_verificacion(huesped, estado_anterior)
        
        messages.warning(request, f'❌ Huésped {huesped.nombres} {huesped.apellidos} rechazado. '
                                f'Notificación enviada a {huesped.user.email or "sin email registrado"}')
        return redirect('admin:core_huesped_changelist')
    
    return redirect('admin:core_huesped_changelist')


@login_required
@user_passes_test(es_administrador)
def solicitar_correccion_huesped(request, pk):
    if request.method == 'POST':
        huesped = get_object_or_404(Huesped, pk=pk)
        comentario = request.POST.get('comentario', '')
        
        if not comentario:
            messages.error(request, 'Debes proporcionar un comentario sobre qué corregir.')
            return redirect('admin:core_huesped_changelist')
        
        estado_anterior = huesped.estado_verificacion
        
        huesped.estado_verificacion = 'requiere_correccion'
        huesped.comentario_verificacion = comentario
        huesped.save()
        
        enviar_notificacion_verificacion(huesped, estado_anterior)
        
        messages.info(request, f'📝 Se ha solicitado corrección para {huesped.nombres} {huesped.apellidos}. '
                             f'Notificación enviada a {huesped.user.email or "sin email registrado"}')
        return redirect('admin:core_huesped_changelist')
    
    return redirect('admin:core_huesped_changelist')


@login_required
@user_passes_test(es_administrador)
def marcar_en_revision_huesped(request, pk):
    if request.method == 'POST':
        huesped = get_object_or_404(Huesped, pk=pk)
        
        huesped.estado_verificacion = 'en_revision'
        huesped.save()
        
        enviar_notificacion_verificacion(huesped)
        
        messages.info(request, f'🔍 Huésped {huesped.nombres} {huesped.apellidos} marcado como "En Revisión".')
        return redirect('admin:core_huesped_changelist')
    
    return redirect('admin:core_huesped_changelist')