from django.urls import path
from .views import registrar_huesped

urlpatterns = [
    path('registro/', registrar_huesped, name='registrar_huesped'),
]