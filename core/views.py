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
from .models import Huesped, Afectado, Match, UBICACIONES, ESTADO_VERIFICACION_CHOICES
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
- ✅ Ver afectados que coinciden con tus condiciones
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
- ✅ Ver huéspedes que coinciden con tus necesidades
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

# ✅ FUNCIÓN PARA ENVIAR NOTIFICACIONES DE MATCH
def enviar_notificacion_match(match, tipo='nueva_solicitud'):
    """
    Envía notificaciones por email relacionadas con matches
    tipos: 'nueva_solicitud', 'solicitud_aceptada', 'solicitud_rechazada', 
           'solicitud_rechazada_por_otro_match', 'match_declinado', 'solicitud_reactivada'
    """
    
    if tipo == 'nueva_solicitud':
        # Notificar al afectado que recibió una solicitud
        if match.afectado.user and match.afectado.user.email:
            try:
                send_mail(
                    subject='📩 Nueva solicitud de contacto - VzlaUnida',
                    message=f"""
Hola {match.afectado.nombres},

Has recibido una nueva solicitud de contacto de un huésped en VzlaUnida.

👤 Huésped: {match.huesped.nombres} {match.huesped.apellidos}
📍 Ubicación: {match.huesped.ciudad}, {match.huesped.estado}
🏠 Capacidad: {match.huesped.cantidad_personas} personas
📋 Tipo de acogida: {match.huesped.tipo_acogida}

Coincidencias:
{'- ✅ Capacidad compatible' if match.coincide_capacidad else '- ❌ Capacidad no compatible'}
{'- ✅ Mascotas compatible' if match.coincide_mascotas else '- ❌ Mascotas no compatible'}

Compatibilidad: {match.porcentaje_compatibilidad}%

Mensaje del huésped:
{match.mensaje or 'Sin mensaje adicional'}

Para aceptar o rechazar esta solicitud, inicia sesión en tu cuenta y revisa tu dashboard.

Saludos,
El equipo de VzlaUnida
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[match.afectado.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error al enviar notificación a {match.afectado.user.email}: {e}")
    
    elif tipo == 'solicitud_aceptada':
        # Notificar al huésped que su solicitud fue aceptada
        if match.huesped.user and match.huesped.user.email:
            try:
                send_mail(
                    subject='✅ Solicitud aceptada - VzlaUnida',
                    message=f"""
Hola {match.huesped.nombres},

¡Excelentes noticias! {match.afectado.nombres} {match.afectado.apellidos} ha ACEPTADO tu solicitud de contacto.

📱 Teléfono del afectado: {match.afectado.telefono}
📍 Ubicación: {match.afectado.ciudad}, {match.afectado.estado}

Ya puedes contactarlo directamente.

Consejos para un contacto seguro:
- Acuerden un lugar público para conocerse primero
- Compartan información de contacto adicional en persona
- Confirma la identidad antes de compartir información sensible

Saludos,
El equipo de VzlaUnida
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[match.huesped.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error al enviar notificación a {match.huesped.user.email}: {e}")
    
    elif tipo == 'solicitud_rechazada':
        # Notificar al huésped que su solicitud fue rechazada por el afectado
        if match.huesped.user and match.huesped.user.email:
            try:
                send_mail(
                    subject='❌ Solicitud rechazada - VzlaUnida',
                    message=f"""
Hola {match.huesped.nombres},

{match.afectado.nombres} {match.afectado.apellidos} ha RECHAZADO tu solicitud de contacto.

No te desanimes, hay muchos otros afectados que podrían necesitar tu ayuda.

Te sugerimos:
- Revisar otros afectados compatibles en tu área
- Ampliar tus condiciones de acogida si es posible
- Seguir buscando, cada persona que ayudas marca la diferencia

Saludos,
El equipo de VzlaUnida
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[match.huesped.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error al enviar notificación a {match.huesped.user.email}: {e}")

    elif tipo == 'solicitud_rechazada_por_otro_match':
        # Notificar al huésped que su solicitud fue rechazada porque el afectado ya tiene match
        if match.huesped.user and match.huesped.user.email:
            try:
                send_mail(
                    subject='❌ Solicitud cancelada - VzlaUnida',
                    message=f"""
Hola {match.huesped.nombres},

Tu solicitud de contacto a {match.afectado.nombres} {match.afectado.apellidos} ha sido CANCELADA.

Motivo: El afectado ya ha aceptado una solicitud de otro huésped.

No te desanimes, hay muchos otros afectados que podrían necesitar tu ayuda.

Te sugerimos:
- Revisar otros afectados compatibles en tu área
- Ampliar tus condiciones de acogida si es posible
- Seguir buscando, cada persona que ayudas marca la diferencia

Saludos,
El equipo de VzlaUnida
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[match.huesped.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error al enviar notificación a {match.huesped.user.email}: {e}")

    elif tipo == 'match_declinado':
        # Notificar al afectado que el match fue declinado
        if match.afectado.user and match.afectado.user.email:
            try:
                send_mail(
                    subject='🔄 Match finalizado - VzlaUnida',
                    message=f"""
Hola {match.afectado.nombres},

El huésped {match.huesped.nombres} {match.huesped.apellidos} ha DECLINADO el match.

Esto significa que:
- ✅ Quedas disponible para otros huéspedes
- ✅ Podrás recibir nuevas solicitudes de contacto
- ✅ El huésped ya no podrá ver tu información

No te preocupes, hay muchos otros huéspedes que pueden ayudarte.

Saludos,
El equipo de VzlaUnida
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[match.afectado.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error al enviar notificación a {match.afectado.user.email}: {e}")

    elif tipo == 'solicitud_reactivada':
        # Notificar al afectado que una solicitud fue reactivada
        if match.afectado.user and match.afectado.user.email:
            try:
                send_mail(
                    subject='🔄 Solicitud reactivada - VzlaUnida',
                    message=f"""
Hola {match.afectado.nombres},

El huésped {match.huesped.nombres} {match.huesped.apellidos} ha DECLINADO un match con otro afectado.

Tu solicitud ha sido REACTIVADA.

Ahora puedes volver a revisar la solicitud y decidir si aceptas o rechazas.

👤 Huésped: {match.huesped.nombres} {match.huesped.apellidos}
📍 Ubicación: {match.huesped.ciudad}, {match.huesped.estado}
🏠 Capacidad: {match.huesped.cantidad_personas} personas

Inicia sesión para revisar tus solicitudes pendientes.

Saludos,
El equipo de VzlaUnida
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[match.afectado.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error al enviar notificación a {match.afectado.user.email}: {e}")


# ✅ FUNCIÓN PARA RECHAZAR OTRAS SOLICITUDES DE CONTACTO
def rechazar_otras_solicitudes(match_aceptado):
    """
    Cuando un afectado acepta una solicitud:
    1. Todas las demás solicitudes PENDIENTES de ese mismo huésped a otros afectados son rechazadas
    2. Todas las demás solicitudes PENDIENTES de otros huéspedes hacia ese mismo afectado son rechazadas
    """
    huesped = match_aceptado.huesped
    afectado = match_aceptado.afectado
    
    # 1. Rechazar todas las solicitudes pendientes del mismo huésped a otros afectados
    otras_solicitudes_del_huesped = Match.objects.filter(
        huesped=huesped,
        estado='pendiente'
    ).exclude(id=match_aceptado.id)
    
    for match in otras_solicitudes_del_huesped:
        match.estado = 'rechazado'
        match.comentario = f'El huésped {huesped.nombres} {huesped.apellidos} ya tiene un match activo con {afectado.nombres} {afectado.apellidos}.'
        match.save()
        enviar_notificacion_match(match, 'solicitud_rechazada')
    
    # 2. Rechazar todas las solicitudes pendientes de otros huéspedes hacia este afectado
    otras_solicitudes_del_afectado = Match.objects.filter(
        afectado=afectado,
        estado='pendiente'
    ).exclude(id=match_aceptado.id)
    
    for match in otras_solicitudes_del_afectado:
        match.estado = 'rechazado'
        match.comentario = f'El afectado {afectado.nombres} {afectado.apellidos} ya tiene un match activo con {huesped.nombres} {huesped.apellidos}.'
        match.save()
        enviar_notificacion_match(match, 'solicitud_rechazada_por_otro_match')


# ✅ FUNCIÓN PARA RESTAURAR SOLICITUDES RECHAZADAS (VERSIÓN CORREGIDA)
def restaurar_solicitudes_rechazadas(huesped, afectado_excluido):
    """
    Cuando un huésped declina un match aceptado, restaura todas las solicitudes
    que fueron rechazadas automáticamente por ese match.
    
    Esto incluye:
    1. Solicitudes del mismo huésped a otros afectados (rechazadas porque el huésped tenía match activo)
    2. Solicitudes de otros huéspedes hacia el afectado declinado (rechazadas porque el afectado tenía match activo)
    """
    # 1. RESTAURAR SOLICITUDES DEL MISMO HUÉSPED A OTROS AFECTADOS
    matches_del_huesped = Match.objects.filter(
        huesped=huesped,
        estado='rechazado'
    ).exclude(afectado=afectado_excluido)
    
    for match in matches_del_huesped:
        if match.comentario and 'ya tiene un match activo con' in match.comentario:
            if not afectado_tiene_match_activo(match.afectado):
                match.estado = 'pendiente'
                match.comentario = None
                match.save()
                enviar_notificacion_match(match, 'solicitud_reactivada')
    
    # 2. RESTAURAR SOLICITUDES DE OTROS HUÉSPEDES HACIA EL AFECTADO DECLINADO
    matches_del_afectado = Match.objects.filter(
        afectado=afectado_excluido,
        estado='rechazado'
    ).exclude(huesped=huesped)
    
    for match in matches_del_afectado:
        if match.comentario and 'ya tiene un match activo con' in match.comentario:
            # Verificar que el afectado sigue disponible (no tiene otro match activo)
            if not afectado_tiene_match_activo(match.afectado):
                match.estado = 'pendiente'
                match.comentario = None
                match.save()
                enviar_notificacion_match(match, 'solicitud_reactivada')


# ✅ FUNCIÓN PARA CALCULAR AFECTADOS COMPATIBLES
def obtener_afectados_compatibles(huesped):
    """Retorna una lista de afectados que cumplen con las condiciones del huésped (sin crear matches)"""
    if huesped.estado_verificacion != 'aprobado':
        return []
    
    afectados_compatibles = []
    
    # ✅ OBTENER IDS DE AFECTADOS QUE EL HUÉSPED YA HA RECHAZADO O TENIDO MATCH
    ids_afectados_rechazados = Match.objects.filter(
        huesped=huesped,
        estado='rechazado'
    ).values_list('afectado_id', flat=True)
    
    # Obtener afectados aprobados que NO estén en la lista de rechazados
    afectados = Afectado.objects.filter(
        estado_verificacion='aprobado'
    ).exclude(id__in=ids_afectados_rechazados)
    
    for afectado in afectados:
        # ✅ VERIFICAR SI EL AFECTADO YA TIENE UN MATCH ACTIVO CON OTRO HUÉSPED
        if afectado_tiene_match_activo(afectado):
            continue
        
        # Verificar si ya existe un match pendiente con este afectado
        match_existente = Match.objects.filter(huesped=huesped, afectado=afectado).first()
        if match_existente:
            # Si el match está pendiente, mostrarlo con el estado
            if match_existente.estado == 'pendiente':
                afectados_compatibles.append({
                    'afectado': afectado,
                    'porcentaje': match_existente.porcentaje_compatibilidad,
                    'coincide_capacidad': match_existente.coincide_capacidad,
                    'coincide_mascotas': match_existente.coincide_mascotas,
                    'match': match_existente,
                    'estado': 'pendiente'
                })
            # Si está rechazado o aceptado, no mostrarlo
            continue
        
        # Verificar condiciones solo si no hay match
        coincide_capacidad = huesped.cantidad_personas >= afectado.cantidad_total()
        coincide_mascotas = False
        if huesped.acepta_mascotas == afectado.tiene_mascotas:
            coincide_mascotas = True
        elif huesped.acepta_mascotas and not afectado.tiene_mascotas:
            coincide_mascotas = True
        
        # Si cumple al menos una condición, agregar a la lista
        if coincide_capacidad or coincide_mascotas:
            puntos = 0
            if coincide_capacidad:
                puntos += 1
            if coincide_mascotas:
                puntos += 1
            porcentaje = int((puntos / 2) * 100)
            
            afectados_compatibles.append({
                'afectado': afectado,
                'porcentaje': porcentaje,
                'coincide_capacidad': coincide_capacidad,
                'coincide_mascotas': coincide_mascotas,
                'match': None,
                'estado': 'sin_contactar'
            })
    
    return afectados_compatibles


# ✅ FUNCIÓN PARA VERIFICAR SI UN HUÉSPED TIENE UN MATCH ACTIVO
def huesped_tiene_match_activo(huesped):
    """Verifica si un huésped tiene un match aceptado"""
    return Match.objects.filter(huesped=huesped, estado='aceptado').exists()


# ✅ FUNCIÓN PARA VERIFICAR SI UN AFECTADO TIENE UN MATCH ACTIVO
def afectado_tiene_match_activo(afectado):
    """Verifica si un afectado tiene un match aceptado"""
    return Match.objects.filter(afectado=afectado, estado='aceptado').exists()


@transaction.atomic
@ratelimit(key='ip', rate=settings.RATELIMIT_REGISTER, method='POST', block=True)
def registrar_huesped(request):
    if request.user.is_authenticated:
        try:
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
        
        # ✅ OBTENER AFECTADOS COMPATIBLES
        tiene_match_activo = huesped_tiene_match_activo(huesped)
        
        afectados_compatibles = []
        matches_pendientes = []
        matches_aceptados = []
        matches_rechazados = []
        
        if huesped.estado_verificacion == 'aprobado' and not tiene_match_activo:
            afectados_compatibles = obtener_afectados_compatibles(huesped)
        
        # Obtener matches existentes
        if huesped.estado_verificacion == 'aprobado':
            matches = Match.objects.filter(huesped=huesped).select_related('afectado')
            matches_pendientes = matches.filter(estado='pendiente')
            matches_aceptados = matches.filter(estado='aceptado')
            matches_rechazados = matches.filter(estado='rechazado')
        
        try:
            total_afectados_estado = Afectado.objects.filter(
                estado=huesped.estado,
                estado_verificacion='aprobado'
            ).count()
            total_afectados_ciudad = Afectado.objects.filter(
                ciudad=huesped.ciudad,
                estado_verificacion='aprobado'
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
            'afectados_compatibles': afectados_compatibles,
            'matches_pendientes': matches_pendientes,
            'matches_aceptados': matches_aceptados,
            'matches_rechazados': matches_rechazados,
            'tiene_match_activo': tiene_match_activo,
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
        
        # ✅ MATCHES - Solicitudes entrantes y aceptadas
        solicitudes_match = []
        matches_aceptados = []
        tiene_match_activo = afectado_tiene_match_activo(afectado)
        
        if afectado.estado_verificacion == 'aprobado':
            matches = Match.objects.filter(afectado=afectado).select_related('huesped')
            
            # Solo mostrar solicitudes pendientes si NO tiene match activo
            if not tiene_match_activo:
                for match in matches.filter(estado='pendiente'):
                    solicitudes_match.append({
                        'match': match,
                        'huesped': match.huesped,
                        'porcentaje': match.porcentaje_compatibilidad,
                        'mensaje': match.mensaje,
                    })
            
            # Matches aceptados (siempre visibles)
            for match in matches.filter(estado='aceptado'):
                matches_aceptados.append({
                    'match': match,
                    'huesped': match.huesped,
                    'telefono': match.huesped.telefono,
                })
        
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
            'solicitudes_match': solicitudes_match,
            'matches_aceptados': matches_aceptados,
            'tiene_match_activo': tiene_match_activo,
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
def ver_detalle_afectado(request, pk):
    """Vista para que el huésped vea el detalle de un afectado"""
    try:
        huesped = Huesped.objects.get(user=request.user)
        afectado = get_object_or_404(Afectado, pk=pk)
        
        # Verificar que el huésped esté aprobado
        if huesped.estado_verificacion != 'aprobado':
            messages.warning(request, 'Debes tener un perfil verificado para ver detalles.')
            return redirect('dashboard_huesped')
        
        # Verificar que el afectado esté aprobado
        if afectado.estado_verificacion != 'aprobado':
            messages.warning(request, 'Este afectado aún no está verificado.')
            return redirect('dashboard_huesped')
        
        # ✅ Si el huésped tiene un match activo, no puede ver detalles de otros afectados
        if huesped_tiene_match_activo(huesped):
            messages.warning(request, 'Ya tienes un match activo. No puedes ver otros afectados.')
            return redirect('dashboard_huesped')
        
        # Obtener el match (si existe)
        match = Match.objects.filter(huesped=huesped, afectado=afectado).first()
        
        # ✅ Verificar si el teléfono está visible (solo si el match está aceptado)
        telefono_visible = False
        if match and match.estado == 'aceptado':
            telefono_visible = True
        
        # ✅ Marcar mensaje de match
        mensaje_match = None
        if match:
            if match.estado == 'aceptado':
                mensaje_match = '✅ Match aceptado - Teléfono visible'
            elif match.estado == 'pendiente':
                mensaje_match = '⏳ Solicitud pendiente - Esperando respuesta'
            elif match.estado == 'rechazado':
                mensaje_match = '❌ Solicitud rechazada'
        
        context = {
            'huesped': huesped,
            'afectado': afectado,
            'match': match,
            'telefono_visible': telefono_visible,
            'mensaje_match': mensaje_match,
        }
        return render(request, 'detalle_afectado.html', context)
        
    except Huesped.DoesNotExist:
        messages.warning(request, 'No tienes un perfil de huésped.')
        return redirect('registrar_huesped')


@login_required
def contactar_afectado(request, pk):
    """Vista para que el huésped envíe una solicitud de contacto a un afectado"""
    try:
        huesped = Huesped.objects.get(user=request.user)
        afectado = get_object_or_404(Afectado, pk=pk)
        
        if huesped.estado_verificacion != 'aprobado':
            messages.warning(request, 'Debes tener un perfil verificado para contactar.')
            return redirect('dashboard_huesped')
        
        if afectado.estado_verificacion != 'aprobado':
            messages.warning(request, 'Este afectado aún no está verificado.')
            return redirect('dashboard_huesped')
        
        # ✅ Si el huésped ya tiene un match activo, no puede contactar a otros
        if huesped_tiene_match_activo(huesped):
            messages.warning(request, 'Ya tienes un match activo. No puedes contactar a otros afectados.')
            return redirect('dashboard_huesped')
        
        # Verificar si ya existe un match
        match, created = Match.objects.get_or_create(
            huesped=huesped,
            afectado=afectado,
            defaults={
                'estado': 'pendiente',
                'mensaje': f'El huésped {huesped.nombres} {huesped.apellidos} de {huesped.ciudad}, {huesped.estado} desea contactarte.'
            }
        )
        
        # Si ya existe y no está pendiente, mostrar mensaje
        if not created and match.estado != 'pendiente':
            messages.info(request, f'Ya existe una solicitud con estado: {match.get_estado_display()}')
            return redirect('detalle_afectado', pk=pk)
        
        # ✅ Si está pendiente o es nuevo, actualizar mensaje
        if created or match.estado == 'pendiente':
            if request.method == 'POST':
                mensaje = request.POST.get('mensaje', '')
                if mensaje:
                    match.mensaje = f"{mensaje}\n\n---\nHuésped: {huesped.nombres} {huesped.apellidos}\nUbicación: {huesped.ciudad}, {huesped.estado}"
                else:
                    match.mensaje = f"El huésped {huesped.nombres} {huesped.apellidos} de {huesped.ciudad}, {huesped.estado} desea contactarte."
                match.save()
            
            # ✅ CALCULAR PORCENTAJE DE COMPATIBILIDAD
            puntos = 0
            if match.huesped.cantidad_personas >= match.afectado.cantidad_total():
                puntos += 1
                match.coincide_capacidad = True
            if match.huesped.acepta_mascotas == match.afectado.tiene_mascotas:
                puntos += 1
                match.coincide_mascotas = True
            elif match.huesped.acepta_mascotas and not match.afectado.tiene_mascotas:
                puntos += 1
                match.coincide_mascotas = True
            match.porcentaje_compatibilidad = int((puntos / 2) * 100)
            match.save()
            
            # ✅ ENVIAR NOTIFICACIÓN AL AFECTADO
            enviar_notificacion_match(match, 'nueva_solicitud')
            
            messages.success(request, '✅ Solicitud de contacto enviada exitosamente. El afectado recibirá una notificación.')
        
        return redirect('dashboard_huesped')
        
    except Huesped.DoesNotExist:
        messages.warning(request, 'No tienes un perfil de huésped.')
        return redirect('registrar_huesped')
    except Exception as e:
        messages.error(request, f'Error al enviar solicitud: {str(e)}')
        return redirect('dashboard_huesped')


@login_required
def responder_match(request, match_id):
    """Vista para que el afectado acepte o rechace una solicitud de contacto"""
    try:
        afectado = Afectado.objects.get(user=request.user)
        match = get_object_or_404(Match, pk=match_id, afectado=afectado)
        
        if request.method == 'POST':
            accion = request.POST.get('accion', '')
            
            if accion == 'aceptar':
                # ✅ Si el afectado ya tiene un match activo, no puede aceptar otro
                if afectado_tiene_match_activo(afectado):
                    messages.warning(request, 'Ya tienes un match activo. No puedes aceptar más solicitudes.')
                    return redirect('dashboard_afectado')
                
                match.estado = 'aceptado'
                match.save()
                
                # ✅ RECHAZAR AUTOMÁTICAMENTE OTRAS SOLICITUDES
                rechazar_otras_solicitudes(match)
                
                messages.success(request, f'✅ Has aceptado la solicitud de {match.huesped.nombres} {match.huesped.apellidos}. Ambos pueden ver sus teléfonos.')
                
                # ✅ Enviar notificación al huésped
                enviar_notificacion_match(match, 'solicitud_aceptada')
                
            elif accion == 'rechazar':
                match.estado = 'rechazado'
                match.comentario = 'Rechazado por el afectado.'
                match.save()
                messages.warning(request, f'❌ Has rechazado la solicitud de {match.huesped.nombres} {match.huesped.apellidos}.')
                
                # ✅ Enviar notificación al huésped
                enviar_notificacion_match(match, 'solicitud_rechazada')
            
            return redirect('dashboard_afectado')
        
        return redirect('dashboard_afectado')
        
    except Afectado.DoesNotExist:
        messages.warning(request, 'No tienes un perfil de afectado.')
        return redirect('registrar_afectado')


@login_required
def declinar_match(request, match_id):
    """Vista para que el huésped decline un match aceptado"""
    try:
        huesped = Huesped.objects.get(user=request.user)
        match = get_object_or_404(Match, pk=match_id, huesped=huesped)
        
        # Solo se puede declinar si el match está aceptado
        if match.estado != 'aceptado':
            messages.warning(request, 'Solo puedes declinar matches aceptados.')
            return redirect('dashboard_huesped')
        
        # ✅ GUARDAR EL AFECTADO PARA LUEGO RESTAURAR SOLICITUDES
        afectado_declinado = match.afectado
        
        # Cambiar estado a 'rechazado'
        match.estado = 'rechazado'
        match.comentario = 'Declinado por el huésped.'
        match.save()
        
        # ✅ RESTAURAR LAS SOLICITUDES QUE FUERON RECHAZADAS AUTOMÁTICAMENTE
        restaurar_solicitudes_rechazadas(huesped, afectado_declinado)
        
        # ✅ Enviar notificación al afectado
        enviar_notificacion_match(match, 'match_declinado')
        
        messages.success(request, '🔄 Has declinado el match. Las solicitudes canceladas han sido restauradas.')
        
        return redirect('dashboard_huesped')
        
    except Huesped.DoesNotExist:
        messages.warning(request, 'No tienes un perfil de huésped.')
        return redirect('registrar_huesped')


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
        
        # ✅ Si el huésped ya tiene un match activo, no puede buscar
        if huesped_tiene_match_activo(huesped):
            messages.warning(request, 'Ya tienes un match activo. No puedes buscar más afectados.')
            return redirect('dashboard_huesped')
        
        estado = request.GET.get('estado', '')
        ciudad = request.GET.get('ciudad', '')
        capacidad_minima = request.GET.get('capacidad_minima', 0)
        
        try:
            afectados = Afectado.objects.filter(estado_verificacion='aprobado')
            
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
        
        # ✅ Si el afectado ya tiene un match activo, no puede buscar
        if afectado_tiene_match_activo(afectado):
            messages.warning(request, 'Ya tienes un match activo. No puedes buscar más huéspedes.')
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