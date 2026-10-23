from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db import transaction
from django.db.models import Count, Q
import json
from .forms import CambiarRolForm, LoginForm, CrearUsuarioForm, EditarUsuarioForm
from .models import PerfilUsuario, Rol, get_rol_nombre, es_administrador, es_coordinador, es_instructor, es_docente_enlace, es_aprendiz
from instituciones.models import InstitucionEducativa
from academico.models import Ficha, Matricula
from seguimiento.models import BitacoraSeguimiento
from evaluaciones.models import JuicioEvaluativo


def _redirect_por_rol(user):
    """Redirige al usuario a la vista correspondiente segun su rol verificado en backend."""
    if es_administrador(user):
        return redirect('panel_admin')
    return redirect('dashboard')


def login_view(request):
    """
    Vista de autenticación segura en la plataforma EduNova.
    La redirección posterior depende del rol verificado en el servidor.
    """
    if request.user.is_authenticated:
        return _redirect_por_rol(request.user)

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # RN-008: Verificar que la cuenta esté activa
            perfil = getattr(user, 'perfil', None)
            if perfil and not perfil.esta_activo:
                messages.error(request, "Su cuenta se encuentra inactiva. Contacte al administrador del sistema.")
                logout(request)
                return render(request, 'login.html', {'form': form})
            login(request, user)
            messages.success(request, f"¡Bienvenido(a) a EduNova, {user.first_name or user.username}!")
            return _redirect_por_rol(user)
        else:
            messages.error(request, "Credenciales no válidas. Por favor verifique su usuario y contraseña.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """
    Cierre de sesión seguro.
    """
    logout(request)
    messages.info(request, "Ha cerrado sesión de forma segura.")
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Panel funcional por rol: administrador global, instructor, docente y aprendiz.
    """
    from datetime import timedelta
    from django.utils import timezone

    rol = get_rol_nombre(request.user)
    if not rol:
        messages.warning(request, 'Su cuenta no tiene un rol asignado. Consulte al administrador.')
        return redirect('login')

    hoy = timezone.now().date()

    if es_aprendiz(request.user):
        matriculas = Matricula.objects.filter(aprendiz=request.user).select_related('ficha', 'ficha__programa', 'ficha__institucion').order_by('-fecha_matricula')[:10]
        return render(request, 'dashboard.html', {
            'rol_actual': rol,
            'dashboard_role': 'aprendiz',
            'matriculas': matriculas,
            'total_matriculas': matriculas.count(),
        })

    if es_docente_enlace(request.user):
        perfil = getattr(request.user, 'perfil', None)
        institucion = perfil.institucion if perfil and perfil.institucion_id else None
        fichas = Ficha.objects.filter(institucion=institucion).select_related('programa', 'institucion').order_by('-fecha_inicio') if institucion else Ficha.objects.none()
        matriculas = Matricula.objects.filter(ficha__institucion=institucion).select_related('aprendiz', 'ficha').order_by('-id')[:8] if institucion else Matricula.objects.none()
        return render(request, 'dashboard.html', {
            'rol_actual': rol,
            'dashboard_role': 'docente',
            'institucion': institucion,
            'fichas': fichas,
            'matriculas': matriculas,
            'total_fichas': fichas.count(),
        })

    if es_instructor(request.user):
        fichas_asignadas = Ficha.objects.filter(instructor_lider=request.user).select_related('programa', 'institucion').order_by('-fecha_inicio')
        matriculas = Matricula.objects.filter(ficha__instructor_lider=request.user).select_related('aprendiz', 'ficha__institucion', 'ficha__programa').order_by('aprendiz__last_name')[:8]
        return render(request, 'dashboard.html', {
            'rol_actual': rol,
            'dashboard_role': 'instructor',
            'fichas_asignadas': fichas_asignadas,
            'matriculas': matriculas,
            'total_fichas': fichas_asignadas.count(),
        })

    total_colegios = InstitucionEducativa.objects.filter(activa=True).count()
    total_instituciones_convenio = InstitucionEducativa.objects.count()
    total_fichas = Ficha.objects.filter(estado__in=['En Ejecucion', 'Activa', 'En cierre']).count()
    total_fichas_activas = total_fichas
    total_aprendices = Matricula.objects.filter(estado_formacion='En Formacion').count()
    total_aprendices_formacion = total_aprendices

    total_aprobados = JuicioEvaluativo.objects.filter(juicio_valor='A').count()
    total_no_aprobados = JuicioEvaluativo.objects.filter(juicio_valor='D').count()
    total_evaluaciones = total_aprobados + total_no_aprobados
    porcentaje_aprobacion = round((total_aprobados / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0

    fichas_por_vencer = Ficha.objects.filter(
        estado__in=['En Ejecucion', 'Activa', 'En cierre'],
        fecha_fin__gte=hoy,
        fecha_fin__lte=hoy + timedelta(days=30),
    ).select_related('institucion', 'programa').order_by('fecha_fin')

    fichas_alerta = []
    for ficha in Ficha.objects.filter(estado__in=['En Ejecucion', 'Activa', 'En cierre']).select_related('institucion'):
        dias_restantes = (ficha.fecha_fin - hoy).days
        if dias_restantes <= 15 and dias_restantes >= 0:
            ultimo_seguimiento = BitacoraSeguimiento.objects.filter(ficha=ficha).order_by('-fecha_visita').first()
            if ultimo_seguimiento is None or (hoy - ultimo_seguimiento.fecha_visita).days > 15:
                fichas_alerta.append(ficha)

    ultimas_bitacoras = BitacoraSeguimiento.objects.select_related(
        'ficha', 'ficha__institucion', 'instructor'
    ).order_by('-fecha_visita', '-id')[:5]

    instituciones_con_alerta = []
    for institucion in InstitucionEducativa.objects.all():
        ultimo = BitacoraSeguimiento.objects.filter(ficha__institucion=institucion).order_by('-fecha_visita').first()
        if ultimo is None:
            dias_sin_seguimiento = 999
        else:
            dias_sin_seguimiento = (hoy - ultimo.fecha_visita).days
        if dias_sin_seguimiento >= 30:
            instituciones_con_alerta.append({
                'institucion': institucion,
                'dias_sin_seguimiento': dias_sin_seguimiento,
                'ultimo': ultimo,
            })

    fichas_recientes = Ficha.objects.select_related(
        'programa', 'institucion', 'instructor_lider'
    ).order_by('-id')[:5]

    fichas_con_juicios = (
        Ficha.objects.filter(estado__in=['En Ejecucion', 'Activa', 'En cierre'])
        .annotate(
            aprobados=Count('matriculas__juicios_evaluativos', filter=Q(matriculas__juicios_evaluativos__juicio_valor='A')),
            no_aprobados=Count('matriculas__juicios_evaluativos', filter=Q(matriculas__juicios_evaluativos__juicio_valor='D')),
        )
        .order_by('codigo_ficha')[:8]
    )
    chart_fichas_labels = json.dumps([f"Ficha {f.codigo_ficha}" for f in fichas_con_juicios])
    chart_fichas_aprobados = json.dumps([f.aprobados for f in fichas_con_juicios])
    chart_fichas_no_aprobados = json.dumps([f.no_aprobados for f in fichas_con_juicios])

    estados_aprendices = (
        Matricula.objects.values('estado_formacion')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    ESTADOS_LABELS = {
        'En Formacion': 'En Formación',
        'Desertado': 'Desertado',
        'Trasladado': 'Trasladado',
        'Retirado': 'Retiro Voluntario',
        'Certificado': 'Certificado',
    }
    chart_estados_labels = json.dumps([ESTADOS_LABELS.get(e['estado_formacion'], e['estado_formacion']) for e in estados_aprendices])
    chart_estados_data = json.dumps([e['total'] for e in estados_aprendices])

    fichas_municipio = (
        Ficha.objects.filter(estado__in=['En Ejecucion', 'Activa', 'En cierre'])
        .values('institucion__municipio')
        .annotate(total=Count('id'))
        .order_by('-total')[:8]
    )
    chart_municipio_labels = json.dumps([m['institucion__municipio'] for m in fichas_municipio])
    chart_municipio_data = json.dumps([m['total'] for m in fichas_municipio])

    context = {
        'rol_actual': rol,
        'dashboard_role': 'administrador',
        'total_colegios': total_colegios,
        'total_instituciones_convenio': total_instituciones_convenio,
        'total_fichas': total_fichas,
        'total_fichas_activas': total_fichas_activas,
        'total_aprendices': total_aprendices,
        'total_aprendices_formacion': total_aprendices_formacion,
        'total_aprobados': total_aprobados,
        'total_no_aprobados': total_no_aprobados,
        'porcentaje_aprobacion': porcentaje_aprobacion,
        'fichas_por_vencer': fichas_por_vencer,
        'fichas_alerta': fichas_alerta,
        'instituciones_con_alerta': instituciones_con_alerta,
        'ultimas_bitacoras': ultimas_bitacoras,
        'fichas_recientes': fichas_recientes,
        'chart_fichas_labels': chart_fichas_labels,
        'chart_fichas_aprobados': chart_fichas_aprobados,
        'chart_fichas_no_aprobados': chart_fichas_no_aprobados,
        'chart_estados_labels': chart_estados_labels,
        'chart_estados_data': chart_estados_data,
        'chart_municipio_labels': chart_municipio_labels,
        'chart_municipio_data': chart_municipio_data,
    }
    return render(request, 'dashboard.html', context)


def _es_administrador(user):
    return user.is_superuser or (
        hasattr(user, 'perfil')
        and user.perfil.rol
        and user.perfil.rol.nombre == 'Administrador'
    )


@login_required
def gestionar_roles_view(request):
    if not _es_administrador(request.user):
        return HttpResponseForbidden('Solo un Administrador puede gestionar roles.')

    perfiles = PerfilUsuario.objects.select_related('usuario', 'rol', 'institucion').order_by(
        'usuario__last_name', 'usuario__first_name', 'usuario__username'
    )
    perfil_seleccionado = None
    form = None

    if request.method == 'POST':
        perfil_seleccionado = PerfilUsuario.objects.select_related('usuario').get(
            pk=request.POST.get('perfil_id')
        )
        form = CambiarRolForm(request.POST, instance=perfil_seleccionado)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Rol de {perfil_seleccionado.usuario.get_full_name() or perfil_seleccionado.usuario.username} actualizado correctamente.'
            )
            return redirect('gestionar_roles')
    elif request.GET.get('perfil'):
        perfil_seleccionado = PerfilUsuario.objects.select_related('usuario').get(
            pk=request.GET['perfil']
        )
        form = CambiarRolForm(instance=perfil_seleccionado)

    return render(request, 'usuarios/gestionar_roles.html', {
        'perfiles': perfiles,
        'perfil_seleccionado': perfil_seleccionado,
        'form': form,
    })


# ════════════════════════════════════════════════════════════════
#  PANEL DEL ADMINISTRADOR GENERAL
# ════════════════════════════════════════════════════════════════

from functools import wraps


def admin_required(view_func):
    """Decorador: solo administradores globales. Devuelve 403 si no lo es."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not es_administrador(request.user):
            return HttpResponseForbidden('No tiene permisos de Administrador para acceder a este módulo.')
        return view_func(request, *args, **kwargs)
    return _wrapped


@admin_required
def panel_admin_view(request):
    """
    Panel principal exclusivo del Administrador General.
    Muestra estadísticas reales del sistema y accesos a módulos.
    """
    from datetime import timedelta
    from django.utils import timezone

    hoy = timezone.now().date()

    # Estadísticas reales
    total_usuarios = User.objects.count()
    total_usuarios_activos = PerfilUsuario.objects.filter(esta_activo=True).count()
    total_admins = PerfilUsuario.objects.filter(rol__nombre='Administrador', esta_activo=True).count()
    total_coordinadores = PerfilUsuario.objects.filter(rol__nombre='Coordinador', esta_activo=True).count()
    total_instructores = PerfilUsuario.objects.filter(rol__nombre='Instructor SENA', esta_activo=True).count()
    total_docentes_enlace = PerfilUsuario.objects.filter(rol__nombre='Docente Enlace', esta_activo=True).count()
    total_aprendices = PerfilUsuario.objects.filter(rol__nombre='Aprendiz', esta_activo=True).count()

    total_instituciones = InstitucionEducativa.objects.count()
    total_instituciones_activas = InstitucionEducativa.objects.filter(activa=True).count()

    total_fichas = Ficha.objects.filter(estado='En Ejecucion').count()
    total_aprendices_formacion = Matricula.objects.filter(estado_formacion='En Formacion').count()

    total_aprobados = JuicioEvaluativo.objects.filter(juicio_valor='A').count()
    total_no_aprobados = JuicioEvaluativo.objects.filter(juicio_valor='D').count()
    total_evaluaciones = total_aprobados + total_no_aprobados
    porcentaje_aprobacion = round((total_aprobados / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0

    total_seguimientos = BitacoraSeguimiento.objects.count()
    seguimientos_recientes = BitacoraSeguimiento.objects.select_related(
        'ficha', 'ficha__institucion', 'instructor'
    ).order_by('-fecha_registro')[:5]

    fichas_recientes = Ficha.objects.select_related(
        'programa', 'institucion', 'instructor_lider'
    ).order_by('-id')[:5]

    # Distribución de roles para gráfico
    roles_distribution = PerfilUsuario.objects.filter(esta_activo=True).values('rol__nombre').annotate(
        total=Count('id')
    ).order_by('-total')

    context = {
        'total_usuarios': total_usuarios,
        'total_usuarios_activos': total_usuarios_activos,
        'total_admins': total_admins,
        'total_coordinadores': total_coordinadores,
        'total_instructores': total_instructores,
        'total_docentes_enlace': total_docentes_enlace,
        'total_aprendices': total_aprendices,
        'total_instituciones': total_instituciones,
        'total_instituciones_activas': total_instituciones_activas,
        'total_fichas': total_fichas,
        'total_aprendices_formacion': total_aprendices_formacion,
        'total_aprobados': total_aprobados,
        'total_no_aprobados': total_no_aprobados,
        'porcentaje_aprobacion': porcentaje_aprobacion,
        'total_seguimientos': total_seguimientos,
        'seguimientos_recientes': seguimientos_recientes,
        'fichas_recientes': fichas_recientes,
        'roles_distribution': list(roles_distribution),
    }
    return render(request, 'usuarios/panel_admin.html', context)


# ════════════════════════════════════════════════════════════════
#  GESTIÓN COMPLETA DE USUARIOS
# ════════════════════════════════════════════════════════════════

@admin_required
def lista_usuarios_view(request):
    """
    Listado de usuarios con buscador y filtro por rol.
    """
    query = request.GET.get('q', '').strip()
    rol_filtro = request.GET.get('rol', '').strip()
    estado_filtro = request.GET.get('estado', '').strip()

    perfiles = PerfilUsuario.objects.select_related('usuario', 'rol', 'institucion').order_by(
        'usuario__last_name', 'usuario__first_name', 'usuario__username'
    )

    if query:
        perfiles = perfiles.filter(
            Q(usuario__first_name__icontains=query) |
            Q(usuario__last_name__icontains=query) |
            Q(usuario__username__icontains=query) |
            Q(usuario__email__icontains=query) |
            Q(numero_documento__icontains=query)
        )

    if rol_filtro:
        perfiles = perfiles.filter(rol__nombre=rol_filtro)

    if estado_filtro == 'activos':
        perfiles = perfiles.filter(esta_activo=True)
    elif estado_filtro == 'inactivos':
        perfiles = perfiles.filter(esta_activo=False)

    roles = Rol.objects.all().order_by('nombre')

    context = {
        'perfiles': perfiles,
        'query': query,
        'rol_filtro': rol_filtro,
        'estado_filtro': estado_filtro,
        'roles': roles,
    }
    return render(request, 'usuarios/lista_usuarios.html', context)


@admin_required
def crear_usuario_view(request):
    """
    Creación de un nuevo usuario con perfil, rol y validación RN-001 (documento único).
    """
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                with transaction.atomic():
                    # RN-001: Verificar documento único
                    num_doc = cd['numero_documento'].strip()
                    if PerfilUsuario.objects.filter(numero_documento=num_doc).exists():
                        messages.error(request, f"Error (RN-001): Ya existe un usuario con el documento {num_doc}.")
                        return render(request, 'usuarios/usuario_form.html', {'form': form, 'titulo': 'Crear Nuevo Usuario'})

                    # Crear usuario Django
                    user = User.objects.create_user(
                        username=cd['username'],
                        email=cd['email'],
                        first_name=cd['first_name'],
                        last_name=cd['last_name'],
                        password=cd['password'],
                    )

                    # Actualizar PerfilUsuario (creado por señal post_save)
                    perfil = user.perfil
                    perfil.rol = cd['rol']
                    perfil.institucion = cd.get('institucion')
                    perfil.tipo_documento = cd['tipo_documento']
                    perfil.numero_documento = num_doc
                    perfil.telefono = cd.get('telefono', '')
                    perfil.esta_activo = True
                    perfil.save()

                    messages.success(
                        request,
                        f'Usuario {user.get_full_name() or user.username} creado exitosamente con rol {perfil.rol.nombre}.'
                    )
                    return redirect('lista_usuarios')

            except Exception as e:
                messages.error(request, f"Ocurrió un error al crear el usuario: {str(e)}")
    else:
        form = CrearUsuarioForm()

    return render(request, 'usuarios/usuario_form.html', {'form': form, 'titulo': 'Crear Nuevo Usuario'})


@admin_required
def editar_usuario_view(request, perfil_id):
    """
    Edición de datos de un usuario existente (nombre, email, teléfono, rol, institución).
    No permite ver ni modificar contraseñas.
    """
    perfil = get_object_or_404(PerfilUsuario.objects.select_related('usuario', 'rol'), pk=perfil_id)

    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=perfil)
        if form.is_valid():
            cd = form.cleaned_data
            user = perfil.usuario
            user.first_name = cd['first_name']
            user.last_name = cd['last_name']
            user.email = cd['email']
            user.save()
            form.save()
            messages.success(request, f'Datos de {user.get_full_name() or user.username} actualizados correctamente.')
            return redirect('lista_usuarios')
    else:
        form = EditarUsuarioForm(instance=perfil, initial={
            'first_name': perfil.usuario.first_name,
            'last_name': perfil.usuario.last_name,
            'email': perfil.usuario.email,
        })

    return render(request, 'usuarios/usuario_form.html', {
        'form': form,
        'titulo': f'Editar Usuario: {perfil.usuario.get_full_name() or perfil.usuario.username}',
        'perfil': perfil,
    })


@admin_required
def toggle_activo_usuario_view(request, perfil_id):
    """
    Activar o desactivar la cuenta de un usuario (RN-008: borrado lógico).
    No permite que el admin se desactive a sí mismo.
    """
    if request.method != 'POST':
        return redirect('lista_usuarios')

    perfil = get_object_or_404(PerfilUsuario, pk=perfil_id)

    # Prevenir auto-desactivación
    if perfil.usuario_id == request.user.id:
        messages.error(request, "No puede desactivar su propia cuenta.")
        return redirect('lista_usuarios')

    perfil.esta_activo = not perfil.esta_activo
    perfil.save()
    estado = "activada" if perfil.esta_activo else "desactivada"
    messages.success(request, f'La cuenta de {perfil.usuario.get_full_name() or perfil.usuario.username} ha sido {estado}.')
    return redirect('lista_usuarios')
