import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.db import models
from .models import Huesped, Afectado, UBICACIONES
from .forms import RegistroUsuarioForm, HuespedRegistrationForm

@transaction.atomic
def registrar_huesped(request):
    """
    Vista para registrar un nuevo huésped.
    Crea usuario y perfil de huésped en una transacción atómica.
    """
    if request.method == 'POST':
        user_form = RegistroUsuarioForm(request.POST)
        huesped_form = HuespedRegistrationForm(request.POST, request.FILES)
        
        if user_form.is_valid() and huesped_form.is_valid():
            try:
                # Crear usuario
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data['password'])
                user.save()
                
                # Crear huésped
                huesped = huesped_form.save(commit=False)
                huesped.user = user
                huesped.telefono = f"{huesped_form.cleaned_data['prefijo_telefono']}{huesped_form.cleaned_data['numero_telefono']}"
                huesped.estado = huesped_form.cleaned_data['estado']
                huesped.ciudad = huesped_form.cleaned_data['ciudad']
                huesped.tiempo_disponible_meses = int(huesped_form.cleaned_data['tiempo_disponible_meses'])
                
                # Asignar cédula con prefijo y número
                huesped.prefijo_cedula = huesped_form.cleaned_data['prefijo_cedula']
                huesped.numero_cedula = huesped_form.cleaned_data['numero_cedula']
                
                huesped.save()
                
                # Iniciar sesión automáticamente
                login(request, user)
                
                # Mensaje de éxito
                messages.success(request, f'¡Bienvenido {huesped.nombres}! Tu registro fue exitoso.')
                
                return redirect('dashboard_huesped')
                
            except Exception as e:
                # Si algo sale mal, eliminar el usuario creado
                if 'user' in locals():
                    user.delete()
                messages.error(request, f'Ocurrió un error: {str(e)}')
                return render(request, 'registro_huesped.html', {
                    'user_form': user_form,
                    'huesped_form': huesped_form,
                    'ubicaciones_json': json.dumps(UBICACIONES)
                })
        else:
            # Los formularios con errores se pasan al template
            messages.error(request, 'Por favor corrige los errores en el formulario.')
            return render(request, 'registro_huesped.html', {
                'user_form': user_form,
                'huesped_form': huesped_form,
                'ubicaciones_json': json.dumps(UBICACIONES)
            })
    
    else:
        # GET request - mostrar formularios vacíos
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
    """
    return render(request, 'home.html')


@login_required
def dashboard_huesped(request):
    """
    Dashboard del huésped con matches y estadísticas.
    """
    try:
        # Obtener el perfil del huésped logueado
        huesped = Huesped.objects.get(user=request.user)
        
        # 1. BUSCAR AFECTADOS CERCANOS (Match principal)
        try:
            afectados_cercanos = Afectado.objects.filter(
                models.Q(ciudad=huesped.ciudad) | models.Q(estado=huesped.estado)
            ).order_by('-id')[:10]
        except:
            afectados_cercanos = []
        
        # 2. CONTAR AFECTADOS POR ESTADO
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
        
        # 3. OTROS HUÉSPEDES CERCANOS
        otros_huespedes = Huesped.objects.filter(
            estado=huesped.estado
        ).exclude(id=huesped.id)[:5]
        
        # 4. ESTADÍSTICAS DEL HUÉSPED
        capacidad_total = (
            huesped.capacidad_ninos + 
            huesped.capacidad_adultos + 
            huesped.capacidad_adultos_mayores
        )
        
        # 5. HUÉSPEDES CON MAYOR CAPACIDAD
        top_huespedes = Huesped.objects.filter(
            estado=huesped.estado
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
            'mensaje_bienvenida': f'¡Bienvenido, {huesped.nombres}!'
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
    """
    Vista para ver y editar el perfil del huésped.
    """
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
    """
    Vista para buscar afectados con filtros avanzados.
    """
    try:
        huesped = Huesped.objects.get(user=request.user)
        
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


# ✅ VISTAS DE LOGIN Y LOGOUT (CORREGIDAS)
def login_view(request):
    """
    Vista para iniciar sesión.
    """
    if request.user.is_authenticated:
        # Si ya está autenticado, redirigir según corresponda
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
            
            # ✅ Verificar si el usuario tiene un perfil de huésped
            try:
                # Intentar obtener el perfil de huésped
                huesped = Huesped.objects.get(user=user)
                messages.success(request, f'¡Bienvenido de vuelta, {huesped.nombres}!')
                return redirect('dashboard_huesped')
            except Huesped.DoesNotExist:
                # Si no tiene perfil de huésped, ir al home
                messages.success(request, f'¡Bienvenido, {user.username}!')
                return redirect('home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    """
    Vista para cerrar sesión.
    """
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('home')