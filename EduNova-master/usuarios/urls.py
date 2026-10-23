from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('panel-admin/', views.panel_admin_view, name='panel_admin'),
    path('usuarios/', views.lista_usuarios_view, name='lista_usuarios'),
    path('usuarios/nuevo/', views.crear_usuario_view, name='crear_usuario'),
    path('usuarios/<int:perfil_id>/editar/', views.editar_usuario_view, name='editar_usuario'),
    path('usuarios/<int:perfil_id>/toggle-activo/', views.toggle_activo_usuario_view, name='toggle_activo_usuario'),
    path('usuarios/roles/', views.gestionar_roles_view, name='gestionar_roles'),
]
