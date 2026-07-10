from django.urls import path
from .views import (
    registrar_huesped,
    registrar_afectado,
    home_seleccion,
    dashboard_huesped,
    dashboard_afectado,
    perfil_huesped,
    perfil_afectado,
    buscar_afectados,
    buscar_huespedes,
    login_view,
    logout_view,
    aprobar_huesped,
    rechazar_huesped,
    solicitar_correccion_huesped,
    marcar_en_revision_huesped,
    aprobar_afectado,
    rechazar_afectado,
    solicitar_correccion_afectado,
    marcar_en_revision_afectado,
)

urlpatterns = [
    # ✅ RUTAS PRINCIPALES
    path('', home_seleccion, name='home'),
    path('registro/huesped/', registrar_huesped, name='registrar_huesped'),
    path('registro/afectado/', registrar_afectado, name='registrar_afectado'),
    path('dashboard/', dashboard_huesped, name='dashboard_huesped'),
    path('dashboard/afectado/', dashboard_afectado, name='dashboard_afectado'),
    path('perfil/', perfil_huesped, name='perfil_huesped'),
    path('perfil/afectado/', perfil_afectado, name='perfil_afectado'),
    path('buscar-afectados/', buscar_afectados, name='buscar_afectados'),
    path('buscar-huespedes/', buscar_huespedes, name='buscar_huespedes'),
    
    # Login y Logout
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Rutas de validación - Huésped
    path('admin/aprobar/huesped/<int:pk>/', aprobar_huesped, name='aprobar_huesped'),
    path('admin/rechazar/huesped/<int:pk>/', rechazar_huesped, name='rechazar_huesped'),
    path('admin/corregir/huesped/<int:pk>/', solicitar_correccion_huesped, name='solicitar_correccion_huesped'),
    path('admin/revision/huesped/<int:pk>/', marcar_en_revision_huesped, name='marcar_en_revision_huesped'),
    
    # Rutas de validación - Afectado
    path('admin/aprobar/afectado/<int:pk>/', aprobar_afectado, name='aprobar_afectado'),
    path('admin/rechazar/afectado/<int:pk>/', rechazar_afectado, name='rechazar_afectado'),
    path('admin/corregir/afectado/<int:pk>/', solicitar_correccion_afectado, name='solicitar_correccion_afectado'),
    path('admin/revision/afectado/<int:pk>/', marcar_en_revision_afectado, name='marcar_en_revision_afectado'),
]