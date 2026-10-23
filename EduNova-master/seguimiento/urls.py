from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_seguimientos, name='seguimiento_lista'),
    path('nuevo/', views.nuevo_seguimiento, name='seguimiento_nuevo'),
    path('<int:pk>/', views.detalle_seguimiento, name='seguimiento_detalle'),
]
