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
from django_ratelimit.decorators import ratelimit
from .models import Huesped, Afectado, UBICACIONES, ESTADO_VERIFICACION_CHOICES
from .forms import RegistroUsuarioForm, HuespedRegistrationForm, AfectadoRegistrationForm

# ✅ FUNCIÓN DE VERIFICACIÓN PARA ADMINISTRADORES
def es_administrador(user):
    return user.is_authenticated and user.is_staff

# ✅ FUNCIÓN PARA ENVIAR NOTIFICACIONES POR EMAIL (HUÉSPED)
def enviar_notificacion_verificacion(huesped, estado_anterior=None):
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

# ✅ FUNCIÓN PARA ENVIAR NOTIFICACIONES POR EMAIL (AFECTADO)
def enviar_notificacion_verificacion_afectado(afectado, estado_anterior=None):
    if not afectado.user or not afectado.user.email:
        return
    
    mensajes = {
        'aprobado': {
            'asunto': '✅ ¡Tu perfil ha sido aprobado!',
            'mensaje': f"""
Hola {afectado.nombres},

¡Excelentes noticias! Tu perfil como afectado en VzlaUnida ha sido APROBADO.

Ya puedes:
- ✅ Ver huéspedes disponibles en tu área
- ✅ Recibir ofertas de alojamiento
- ✅ Conectar con personas que pueden ayudarte

Tu núcleo familiar: {afectado.cantidad_total()} personas
Ubicación: {afectado.ciudad}, {afectado.estado}

Gracias por confiar en VzlaUnida.

Saludos,
El equipo de VzlaUnida
"""
        },
        'rechazado': {
            'asunto': '❌ Tu perfil ha sido rechazado',
            'mensaje': f"""
Hola {afectado.nombres},

Lamentamos informarte que tu perfil como afectado en VzlaUnida ha sido RECHAZADO.

Motivo: {afectado.comentario_verificacion or 'No se especificó motivo.'}

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
Hola {afectado.nombres},

Tu perfil como afectado en VzlaUnida requiere algunas correcciones.

Comentario del administrador:
{afectado.comentario_verificacion}

Por favor, inicia sesión en tu cuenta y actualiza la información según lo indicado.

Saludos,
El equipo de VzlaUnida
"""
        },
        'en_revision': {
            'asunto': '🔍 Tu perfil está en revisión',
            'mensaje': f"""
Hola {afectado.nombres},

Te informamos que tu perfil como afectado en VzlaUnida está siendo revisado por nuestro equipo.

Este proceso puede tomar hasta 48 horas. Te notificaremos cuando tengamos una respuesta.

Gracias por tu paciencia.

Saludos,
El equipo de VzlaUnida
"""
        }
    }
    
    info = mensajes.get(afectado.estado_verificacion)
    if not info:
        return
    
    try:
        send_mail(
            subject=info['asunto'],
            message=info['mensaje'],
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[afectado.user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error al enviar notificación a {afectado.user.email}: {e}")


@transaction.atomic
@ratelimit(key='ip', rate=settings.RATELIMIT_REGISTER, method='POST', block=True)
def registrar_huesped(request):
    if request.user.is_authenticated:
        try:
            # Verificar si el usuario ya es afectado
            Afectado.objects.get(user=request.user)
            messages.warning(request, 'Ya tienes un perfil de afectado. No puedes registrarte como huésped.')
            return redirect('dashboard_afectado')
        except Afectado.DoesNotExist:
            pass
        
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


@transaction.atomic
@ratelimit(key='ip', rate=settings.RATELIMIT_REGISTER, method='POST', block=True)
def registrar_afectado(request):
    if request.user.is_authenticated:
        try:
            # Verificar si el usuario ya es huésped
            Huesped.objects.get(user=request.user)
            messages.warning(request, 'Ya tienes un perfil de huésped. No puedes registrarte como afectado.')
            return redirect('dashboard_huesped')
        except Huesped.DoesNotExist:
            pass
        
        try:
            afectado = Afectado.objects.get(user=request.user)
            messages.info(request, 'Ya tienes un perfil de afectado registrado.')
            return redirect('dashboard_afectado')
        except Afectado.DoesNotExist:
            messages.warning(request, 'Ya has iniciado sesión. Si quieres registrar un afectado, contacta al administrador.')
            return redirect('home')
    
    if request.method == 'POST':
        user_form = RegistroUsuarioForm(request.POST)
        afectado_form = AfectadoRegistrationForm(request.POST, request.FILES)
        
        if user_form.is_valid() and afectado_form.is_valid():
            try:
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data['password'])
                user.email = user_form.cleaned_data['email']
                user.save()
                
                afectado = afectado_form.save(commit=False)
                afectado.user = user
                afectado.telefono = f"{afectado_form.cleaned_data['prefijo_telefono']}{afectado_form.cleaned_data['numero_telefono']}"
                afectado.estado = afectado_form.cleaned_data['estado']
                afectado.ciudad = afectado_form.cleaned_data['ciudad']
                
                afectado.prefijo_cedula = afectado_form.cleaned_data['prefijo_cedula']
                afectado.numero_cedula = afectado_form.cleaned_data['numero_cedula']
                
                afectado.cantidad_ninos = int(afectado_form.cleaned_data['cantidad_ninos'])
                afectado.cantidad_adultos = int(afectado_form.cleaned_data['cantidad_adultos'])
                afectado.cantidad_adultos_mayores = int(afectado_form.cleaned_data['cantidad_adultos_mayores'])
                
                afectado.estado_verificacion = 'pendiente'
                
                afectado.save()
                
                if user.email:
                    try:
                        send_mail(
                            subject='✅ Registro exitoso en VzlaUnida',
                            message=f"""
Hola {afectado.nombres},

¡Bienvenido a VzlaUnida! Tu registro como afectado ha sido exitoso.

📋 Estado actual: Pendiente de verificación
⏳ Tiempo estimado: 24-48 horas

Una vez que nuestro equipo verifique tus documentos, recibirás una notificación.

Gracias por confiar en VzlaUnida.

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
                    f'¡Bienvenido {afectado.nombres}! Tu registro fue exitoso. '
                    'Te hemos enviado un correo de confirmación. '
                    'Tu perfil está pendiente de verificación.'
                )
                
                return redirect('dashboard_afectado')
                
            except Exception as e:
                if 'user' in locals():
                    user.delete()
                messages.error(request, f'Ocurrió un error: {str(e)}')
                return render(request, 'registro_afectado.html', {
                    'user_form': user_form,
                    'afectado_form': afectado_form,
                    'ubicaciones_json': json.dumps(UBICACIONES)
                })
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
            return render(request, 'registro_afectado.html', {
                'user_form': user_form,
                'afectado_form': afectado_form,
                'ubicaciones_json': json.dumps(UBICACIONES)
            })
    
    else:
        user_form = RegistroUsuarioForm()
        afectado_form = AfectadoRegistrationForm()
    
    return render(request, 'registro_afectado.html', {
        'user_form': user_form,
        'afectado_form': afectado_form,
        'ubicaciones_json': json.dumps(UBICACIONES)
    })


def home_seleccion(request):
    if request.user.is_authenticated:
        try:
            Huesped.objects.get(user=request.user)
            messages.info(request, 'Ya has iniciado sesión.')
            return redirect('dashboard_huesped')
        except Huesped.DoesNotExist:
            pass
        
        try:
            Afectado.objects.get(user=request.user)
            messages.info(request, 'Ya has iniciado sesión.')
            return redirect('dashboard_afectado')
        except Afectado.DoesNotExist:
            pass
        
        messages.info(request, 'Ya has iniciado sesión como administrador.')
        return redirect('home')
    
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
        
        capacidad_total = huesped.cantidad_personas
        
        top_huespedes = Huesped.objects.filter(
            estado=huesped.estado,
            estado_verificacion='aprobado'
        ).exclude(id=huesped.id).order_by(
            '-cantidad_personas'
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
def dashboard_afectado(request):
    try:
        afectado = Afectado.objects.get(user=request.user)
        
        estado_info = {
            'clase': '',
            'icono': '',
            'mensaje': '',
            'color': ''
        }
        
        if afectado.estado_verificacion == 'aprobado':
            estado_info = {
                'clase': 'bg-green-100 text-green-800 border-green-300',
                'icono': '✅',
                'mensaje': '¡Tu perfil ha sido verificado! Ya puedes buscar alojamiento.',
                'color': 'verde'
            }
        elif afectado.estado_verificacion == 'rechazado':
            estado_info = {
                'clase': 'bg-red-100 text-red-800 border-red-300',
                'icono': '❌',
                'mensaje': 'Tu perfil ha sido rechazado. Por favor contacta al administrador.',
                'color': 'rojo'
            }
        elif afectado.estado_verificacion == 'en_revision':
            estado_info = {
                'clase': 'bg-blue-100 text-blue-800 border-blue-300',
                'icono': '🔍',
                'mensaje': 'Tu perfil está siendo revisado por el administrador. Pronto recibirás respuesta.',
                'color': 'azul'
            }
        elif afectado.estado_verificacion == 'requiere_correccion':
            estado_info = {
                'clase': 'bg-orange-100 text-orange-800 border-orange-300',
                'icono': '📝',
                'mensaje': f'Tu perfil requiere correcciones: {afectado.comentario_verificacion or "Por favor revisa los documentos."}',
                'color': 'naranja'
            }
        else:
            estado_info = {
                'clase': 'bg-yellow-100 text-yellow-800 border-yellow-300',
                'icono': '⏳',
                'mensaje': 'Tu perfil está pendiente de verificación. El administrador revisará tus documentos.',
                'color': 'amarillo'
            }
        
        # Buscar huéspedes cercanos
        huespedes_cercanos = []
        if afectado.estado_verificacion == 'aprobado':
            try:
                huespedes_cercanos = Huesped.objects.filter(
                    models.Q(ciudad=afectado.ciudad) | models.Q(estado=afectado.estado),
                    estado_verificacion='aprobado'
                ).order_by('-cantidad_personas')[:10]
            except:
                huespedes_cercanos = []
        
        try:
            total_huespedes_estado = Huesped.objects.filter(
                estado=afectado.estado,
                estado_verificacion='aprobado'
            ).count()
            total_huespedes_ciudad = Huesped.objects.filter(
                ciudad=afectado.ciudad,
                estado_verificacion='aprobado'
            ).count()
        except:
            total_huespedes_estado = 0
            total_huespedes_ciudad = 0
        
        cantidad_total = afectado.cantidad_total()
        
        context = {
            'afectado': afectado,
            'huespedes_cercanos': huespedes_cercanos,
            'cantidad_total': cantidad_total,
            'total_huespedes_estado': total_huespedes_estado,
            'total_huespedes_ciudad': total_huespedes_ciudad,
            'mensaje_bienvenida': f'¡Bienvenido, {afectado.nombres}!',
            'estado_info': estado_info,
        }
        
        return render(request, 'dashboard_afectado.html', context)
        
    except Afectado.DoesNotExist:
        messages.warning(request, 'No tienes un perfil de afectado completo.')
        return redirect('registrar_afectado')
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
            'capacidad_total': huesped.cantidad_personas
        }
        return render(request, 'perfil_huesped.html', context)
        
    except Huesped.DoesNotExist:
        messages.warning(request, 'No tienes un perfil de huésped.')
        return redirect('registrar_huesped')


@login_required
def perfil_afectado(request):
    try:
        afectado = Afectado.objects.get(user=request.user)
        
        context = {
            'afectado': afectado,
            'cantidad_total': afectado.cantidad_total()
        }
        return render(request, 'perfil_afectado.html', context)
        
    except Afectado.DoesNotExist:
        messages.warning(request, 'No tienes un perfil de afectado.')
        return redirect('registrar_afectado')


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


@login_required
def buscar_huespedes(request):
    try:
        afectado = Afectado.objects.get(user=request.user)
        
        if afectado.estado_verificacion != 'aprobado':
            messages.warning(
                request, 
                'Tu perfil debe estar verificado para buscar huéspedes. '
                'Estado actual: ' + dict(ESTADO_VERIFICACION_CHOICES).get(afectado.estado_verificacion, afectado.estado_verificacion)
            )
            return redirect('dashboard_afectado')
        
        estado = request.GET.get('estado', '')
        ciudad = request.GET.get('ciudad', '')
        capacidad_minima = request.GET.get('capacidad_minima', 0)
        
        try:
            huespedes = Huesped.objects.filter(estado_verificacion='aprobado')
            
            if estado:
                huespedes = huespedes.filter(estado=estado)
            if ciudad:
                huespedes = huespedes.filter(ciudad=ciudad)
            
            huespedes = huespedes.order_by('-cantidad_personas')
        except:
            huespedes = []
        
        context = {
            'afectado': afectado,
            'huespedes': huespedes,
            'filtros': {
                'estado': estado,
                'ciudad': ciudad,
                'capacidad_minima': capacidad_minima,
            }
        }
        return render(request, 'buscar_huespedes.html', context)
        
    except Afectado.DoesNotExist:
        messages.warning(request, 'No tienes un perfil de afectado.')
        return redirect('registrar_afectado')


@ratelimit(key='ip', rate=settings.RATELIMIT_LOGIN, method='POST', block=True)
def login_view(request):
    if request.user.is_authenticated:
        try:
            Huesped.objects.get(user=request.user)
            return redirect('dashboard_huesped')
        except Huesped.DoesNotExist:
            pass
        
        try:
            Afectado.objects.get(user=request.user)
            return redirect('dashboard_afectado')
        except Afectado.DoesNotExist:
            pass
        
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            try:
                Huesped.objects.get(user=user)
                messages.success(request, f'¡Bienvenido de vuelta, {user.username}!')
                return redirect('dashboard_huesped')
            except Huesped.DoesNotExist:
                pass
            
            try:
                Afectado.objects.get(user=user)
                messages.success(request, f'¡Bienvenido de vuelta, {user.username}!')
                return redirect('dashboard_afectado')
            except Afectado.DoesNotExist:
                pass
            
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


# ✅ VISTAS DE VALIDACIÓN PARA HUÉSPED
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


# ✅ VISTAS DE VALIDACIÓN PARA AFECTADO
@login_required
@user_passes_test(es_administrador)
def aprobar_afectado(request, pk):
    if request.method == 'POST':
        afectado = get_object_or_404(Afectado, pk=pk)
        estado_anterior = afectado.estado_verificacion
        
        afectado.estado_verificacion = 'aprobado'
        afectado.fecha_verificacion = timezone.now()
        afectado.comentario_verificacion = request.POST.get('comentario', 'Aprobado por administrador.')
        afectado.save()
        
        enviar_notificacion_verificacion_afectado(afectado, estado_anterior)
        
        messages.success(request, f'✅ Afectado {afectado.nombres} {afectado.apellidos} aprobado. '
                                f'Notificación enviada a {afectado.user.email or "sin email registrado"}')
        return redirect('admin:core_afectado_changelist')
    
    return redirect('admin:core_afectado_changelist')


@login_required
@user_passes_test(es_administrador)
def rechazar_afectado(request, pk):
    if request.method == 'POST':
        afectado = get_object_or_404(Afectado, pk=pk)
        estado_anterior = afectado.estado_verificacion
        
        afectado.estado_verificacion = 'rechazado'
        afectado.fecha_verificacion = timezone.now()
        afectado.comentario_verificacion = request.POST.get('comentario', 'Rechazado por administrador.')
        afectado.save()
        
        enviar_notificacion_verificacion_afectado(afectado, estado_anterior)
        
        messages.warning(request, f'❌ Afectado {afectado.nombres} {afectado.apellidos} rechazado. '
                                f'Notificación enviada a {afectado.user.email or "sin email registrado"}')
        return redirect('admin:core_afectado_changelist')
    
    return redirect('admin:core_afectado_changelist')


@login_required
@user_passes_test(es_administrador)
def solicitar_correccion_afectado(request, pk):
    if request.method == 'POST':
        afectado = get_object_or_404(Afectado, pk=pk)
        comentario = request.POST.get('comentario', '')
        
        if not comentario:
            messages.error(request, 'Debes proporcionar un comentario sobre qué corregir.')
            return redirect('admin:core_afectado_changelist')
        
        estado_anterior = afectado.estado_verificacion
        
        afectado.estado_verificacion = 'requiere_correccion'
        afectado.comentario_verificacion = comentario
        afectado.save()
        
        enviar_notificacion_verificacion_afectado(afectado, estado_anterior)
        
        messages.info(request, f'📝 Se ha solicitado corrección para {afectado.nombres} {afectado.apellidos}. '
                             f'Notificación enviada a {afectado.user.email or "sin email registrado"}')
        return redirect('admin:core_afectado_changelist')
    
    return redirect('admin:core_afectado_changelist')


@login_required
@user_passes_test(es_administrador)
def marcar_en_revision_afectado(request, pk):
    if request.method == 'POST':
        afectado = get_object_or_404(Afectado, pk=pk)
        
        afectado.estado_verificacion = 'en_revision'
        afectado.save()
        
        enviar_notificacion_verificacion_afectado(afectado)
        
        messages.info(request, f'🔍 Afectado {afectado.nombres} {afectado.apellidos} marcado como "En Revisión".')
        return redirect('admin:core_afectado_changelist')
    
    return redirect('admin:core_afectado_changelist')