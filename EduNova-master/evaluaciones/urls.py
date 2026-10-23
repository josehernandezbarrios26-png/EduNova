from django.urls import path
from . import views

urlpatterns = [
    path('boletines/', views.boletines_lista, name='evaluaciones_boletines'),
    path('', views.sabana_calificaciones, name='evaluaciones_calificar'),
    path('boletin/<int:matricula_id>/', views.boletin_aprendiz, name='evaluaciones_boletin'),
    path('boletin/<int:matricula_id>/pdf/', views.boletin_exportar_pdf, name='evaluaciones_boletin_pdf'),
    path('boletin/<int:matricula_id>/xlsx/', views.boletin_exportar_xlsx, name='evaluaciones_boletin_xlsx'),
    path('cerrar-periodo/<int:ficha_id>/', views.cerrar_periodo_ficha, name='evaluaciones_cerrar_periodo'),
]
