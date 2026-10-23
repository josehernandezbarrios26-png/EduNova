from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.db import transaction
from .models import Asistencia, Ficha, Matricula, ProgramaFormacion
from .forms import AsistenciaForm, FichaForm, MatriculaRapidaForm
from usuarios.models import PerfilUsuario, Rol, get_rol_nombre, es_administrador, es_coordinador, es_instructor, es_docente_enlace, es_aprendiz
from edunova_project.correos import enviar_constancia_matricula


@login_required
def lista_fichas(request):
    """
    Listado de Fichas de Media Técnica filtrado por rol del usuario.
    Admin/Coordinador: todas las fichas. Instructor: solo sus fichas asignadas.
    Docente Enlace: fichas de su institución. Aprendiz: no tiene acceso.
    """
    rol = get_rol_nombre(request.user)

    # Aprendices no tienen acceso a este módulo
    if es_aprendiz(request.user):
        return HttpResponseForbidden('Los aprendices no tienen acceso al módulo de fichas.')

    query = request.GET.get('q', '').strip()
    estado_filtro = request.GET.get('estado', '').strip()

    fichas = Ficha.objects.select_related('programa', 'institucion', 'instructor_lider').all()

    # Filtrar por rol: instructor solo ve sus fichas
    if es_instructor(request.user):
        fichas = fichas.filter(instructor_lider=request.user)
    elif es_docente_enlace(request.user):
        perfil = getattr(request.user, 'perfil', None)
        if perfil and perfil.institucion_id:
            fichas = fichas.filter(institucion_id=perfil.institucion_id)
        else:
            fichas = fichas.none()
    # Admin y Coordinador ven todas las fichas

    if query:
        fichas = fichas.filter(
            Q(codigo_ficha__icontains=query) |
            Q(programa__denominacion__icontains=query) |
            Q(institucion__nombre__icontains=query)
        )

    if estado_filtro:
        fichas = fichas.filter(estado=estado_filtro)

    context = {
        'fichas': fichas,
        'query': query,
        'estado_filtro': estado_filtro,
    }
    return render(request, 'academico/fichas_lista.html', context)


@login_required
def detalle_ficha(request, pk):
    """
    Expediente completo de una ficha técnica: aprendices matriculados,
    competencias curriculares y bitácoras de seguimiento asociadas.
    Filtrado por permisos del rol.
    """
    ficha = get_object_or_404(Ficha.objects.select_related('programa', 'institucion', 'instructor_lider'), pk=pk)
    rol = get_rol_nombre(request.user)

    # Verificar permisos de acceso a esta ficha
    if es_instructor(request.user) and ficha.instructor_lider_id != request.user.id:
        return HttpResponseForbidden('No tiene permisos para consultar esta ficha.')
    if es_docente_enlace(request.user):
        perfil = getattr(request.user, 'perfil', None)
        if not perfil or perfil.institucion_id != ficha.institucion_id:
            return HttpResponseForbidden('No tiene permisos para consultar esta ficha.')
    if es_aprendiz(request.user):
        # Un aprendiz solo puede ver la ficha si está matriculado en ella
        if not Matricula.objects.filter(ficha=ficha, aprendiz=request.user).exists():
            return HttpResponseForbidden('No tiene permisos para consultar esta ficha.')

    matriculas = ficha.matriculas.select_related('aprendiz', 'aprendiz__perfil').order_by('aprendiz__last_name')
    seguimientos = ficha.seguimientos.select_related('instructor', 'matricula__aprendiz').order_by('-fecha_visita')[:5]
    competencias = ficha.programa.competencias.prefetch_related('resultados').all()

    context = {
        'ficha': ficha,
        'matriculas': matriculas,
        'seguimientos': seguimientos,
        'competencias': competencias,
    }
    return render(request, 'academico/ficha_detalle.html', context)


def _puede_registrar_asistencia(user):
    roles_permitidos = {'Administrador', 'Coordinador', 'Instructor SENA'}
    return user.is_superuser or (
        hasattr(user, 'perfil') and get_rol_nombre(user) in roles_permitidos
    )


@login_required
def gestionar_asistencia(request, ficha_id):
    ficha = get_object_or_404(Ficha, pk=ficha_id)
    if not _puede_registrar_asistencia(request.user):
        return HttpResponseForbidden('Solo docentes e instructores autorizados pueden registrar asistencias.')
    if get_rol_nombre(request.user) == 'Instructor SENA' and ficha.instructor_lider_id != request.user.id:
        return HttpResponseForbidden('No tiene permisos para registrar asistencia en esta ficha.')

    matriculas = ficha.matriculas.select_related('aprendiz', 'aprendiz__perfil').order_by(
        'aprendiz__last_name', 'aprendiz__first_name'
    )
    matricula_id = request.POST.get('matricula_id') if request.method == 'POST' else request.GET.get('matricula')
    matricula = get_object_or_404(matriculas, pk=matricula_id) if matricula_id else None

    if request.method == 'POST':
        asistencia = Asistencia.objects.filter(matricula=matricula, fecha=request.POST.get('fecha')).first()
        form = AsistenciaForm(request.POST, instance=asistencia)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.matricula = matricula
            registro.registrado_por = request.user
            registro.save()
            messages.success(request, 'Asistencia guardada correctamente.')
            return redirect('asistencia_gestionar', ficha_id=ficha.id)
    else:
        form = AsistenciaForm()

    asistencias = Asistencia.objects.filter(matricula__ficha=ficha).select_related(
        'matricula__aprendiz', 'registrado_por'
    )[:30]
    return render(request, 'academico/asistencia.html', {
        'ficha': ficha,
        'matriculas': matriculas,
        'form': form,
        'matricula_seleccionada': matricula,
        'asistencias': asistencias,
    })


@login_required
def crear_ficha(request):
    """
    Apertura de una nueva ficha técnica de Media Técnica.
    """
    rol = get_rol_nombre(request.user)
    if rol not in {'Administrador', 'Coordinador'}:
        return HttpResponseForbidden('No tiene permisos para crear fichas.')

    if request.method == 'POST':
        form = FichaForm(request.POST)
        if form.is_valid():
            ficha = form.save()
            messages.success(request, f"Ficha {ficha.codigo_ficha} creada exitosamente.")
            return redirect('fichas_detalle', pk=ficha.pk)
        else:
            messages.error(request, "Por favor revise los campos obligatorios.")
    else:
        form = FichaForm()

    return render(request, 'academico/ficha_formulario.html', {'form': form, 'titulo': 'Apertura de Ficha Técnica'})


@login_required
def matricular_aprendiz(request, ficha_id):
    """
    Matrícula de un nuevo estudiante en una ficha técnica (RN-001, RN-002, RN-007).
    Crea el usuario, su perfil y la vinculación formal en una sola transacción segura.
    """
    ficha = get_object_or_404(Ficha, pk=ficha_id)
    rol = get_rol_nombre(request.user)
    if rol not in {'Administrador', 'Coordinador'} and not (rol == 'Instructor SENA' and ficha.instructor_lider_id == request.user.id):
        return HttpResponseForbidden('No tiene permisos para matricular aprendices en esta ficha.')

    if request.method == 'POST':
        form = MatriculaRapidaForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                with transaction.atomic():
                    # Verificar si ya existe usuario con ese correo o documento
                    num_doc = cd['numero_documento'].strip()
                    if PerfilUsuario.objects.filter(numero_documento=num_doc).exists():
                        messages.error(request, f"Error (RN-001): Ya existe un usuario registrado con el documento {num_doc}.")
                        return render(request, 'academico/matricular.html', {'form': form, 'ficha': ficha})

                    rol_aprendiz, _ = Rol.objects.get_or_create(
                        nombre="Aprendiz",
                        defaults={'descripcion': 'Aprendiz matriculado en Media Técnica'}
                    )

                    # Crear usuario Django
                    username = f"ap_{num_doc}"
                    user = User.objects.create_user(
                        username=username,
                        email=cd['correo'],
                        first_name=cd['nombres'],
                        last_name=cd['apellidos'],
                        password=f"Sena{num_doc[:4]}*"  # Contraseña inicial segura
                    )

                    # Actualizar PerfilUsuario
                    perfil = user.perfil
                    perfil.rol = rol_aprendiz
                    perfil.tipo_documento = cd['tipo_documento']
                    perfil.numero_documento = num_doc
                    perfil.telefono = cd['telefono']
                    perfil.save()

                    # Crear Matrícula en la ficha (RN-007)
                    matricula = Matricula.objects.create(
                        ficha=ficha,
                        aprendiz=user,
                        grado_escolar=cd['grado_escolar'],
                        acudiente_nombre=cd['acudiente_nombre'],
                        acudiente_telefono=cd['acudiente_telefono']
                    )

                    messages.success(request, f"Aprendiz {user.get_full_name()} matriculado exitosamente en la Ficha {ficha.codigo_ficha}.")
                    # Enviar constancia de matrícula por correo al aprendiz
                    enviar_constancia_matricula(matricula)
                    return redirect('fichas_detalle', pk=ficha.pk)

            except Exception as e:
                messages.error(request, f"Ocurrió un error al procesar la matrícula: {str(e)}")
    else:
        form = MatriculaRapidaForm()

    return render(request, 'academico/matricular.html', {'form': form, 'ficha': ficha})
