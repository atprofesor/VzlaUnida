from django.urls import path
from .views import registrar_huesped

urlpatterns = [
    path('registro/', registrar_huesped, name='registrar_huesped'),
    # Agregamos esta línea para evitar el error de redirección
    path('registro/exitoso/', registrar_huesped, name='registro_exitoso'), 
]