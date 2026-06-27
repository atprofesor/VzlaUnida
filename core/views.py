from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import HuespedRegistrationForm

def registrar_huesped(request):
    if request.method == 'POST':
        form = HuespedRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            huesped = form.save(commit=False)
            if request.user.is_authenticated:
                huesped.user = request.user
            huesped.save()
            messages.success(request, "¡Registro exitoso!")
            return render(request, 'registro_huesped.html', {'form': HuespedRegistrationForm(), 'mensaje': 'Registro exitoso'})
    else:
        form = HuespedRegistrationForm()
    return render(request, 'registro_huesped.html', {'form': form})