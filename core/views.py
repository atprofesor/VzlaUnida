import json
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import HuespedRegistrationForm
from .models import UBICACIONES

def registrar_huesped(request):
    if request.method == 'POST':
        form = HuespedRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            huesped = form.save(commit=False)
            if request.user.is_authenticated:
                huesped.user = request.user
            huesped.save()
            messages.success(request, "¡Registro exitoso!")
            # Redirigimos a la misma vista para limpiar el formulario y evitar el Broken pipe
            return redirect('registrar_huesped') 
        else:
            # Opcional: imprimir errores en consola para ayudarte a debuguear si el form no es válido
            print(form.errors)
    else:
        form = HuespedRegistrationForm()

    context = {
        'form': form,
        'ubicaciones_json': json.dumps(UBICACIONES)
    }
    
    return render(request, 'registro_huesped.html', context)