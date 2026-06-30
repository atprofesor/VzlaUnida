from django.urls import path
from .views import (
    registrar_huesped, 
    home_seleccion, 
    dashboard_huesped,
    perfil_huesped,
    buscar_afectados,
    login_view,
    logout_view
)

urlpatterns = [
    path('', home_seleccion, name='home'),
    path('registro/huesped/', registrar_huesped, name='registrar_huesped'),
    path('dashboard/', dashboard_huesped, name='dashboard_huesped'),
    path('perfil/', perfil_huesped, name='perfil_huesped'),
    path('buscar-afectados/', buscar_afectados, name='buscar_afectados'),
    
    # ✅ LOGIN Y LOGOUT
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]