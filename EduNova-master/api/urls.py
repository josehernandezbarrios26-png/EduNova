"""
EduNova - URLs de la API REST
Base: /api/
"""

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard / Métricas generales
    path('dashboard/', views.ResumenDashboardAPIView.as_view(), name='api_dashboard'),

    # Fichas
    path('fichas/', views.FichasListAPIView.as_view(), name='api_fichas_lista'),
    path('fichas/<int:pk>/', views.FichaDetalleAPIView.as_view(), name='api_ficha_detalle'),
    path('fichas/<int:pk>/aprendices/', views.AprendicesFichaAPIView.as_view(), name='api_ficha_aprendices'),
    path('fichas/<int:pk>/calificaciones/', views.CalificacionesFichaAPIView.as_view(), name='api_ficha_calificaciones'),

    # Instituciones
    path('instituciones/', views.InstitucionesAPIView.as_view(), name='api_instituciones'),

    # Seguimientos
    path('seguimientos/', views.BitacorasAPIView.as_view(), name='api_seguimientos'),
]
