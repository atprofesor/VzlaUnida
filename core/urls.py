from django.urls import path
from .views import (
    registrar_huesped, 
    home_seleccion, 
    dashboard_huesped,
    perfil_huesped,
    buscar_afectados,
    login_view,
    logout_view,
    aprobar_huesped,
    rechazar_huesped,
    solicitar_correccion_huesped,
    marcar_en_revision_huesped,
)

urlpatterns = [
    # ✅ RUTAS PRINCIPALES
    path('', home_seleccion, name='home'),
    path('registro/huesped/', registrar_huesped, name='registrar_huesped'),
    path('dashboard/', dashboard_huesped, name='dashboard_huesped'),  # ✅ SIN 'registro/'
    path('perfil/', perfil_huesped, name='perfil_huesped'),
    path('buscar-afectados/', buscar_afectados, name='buscar_afectados'),
    
    # Login y Logout
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Rutas de validación (solo administradores)
    path('admin/aprobar/<int:pk>/', aprobar_huesped, name='aprobar_huesped'),
    path('admin/rechazar/<int:pk>/', rechazar_huesped, name='rechazar_huesped'),
    path('admin/corregir/<int:pk>/', solicitar_correccion_huesped, name='solicitar_correccion_huesped'),
    path('admin/revision/<int:pk>/', marcar_en_revision_huesped, name='marcar_en_revision_huesped'),
]