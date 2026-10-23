from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import BitacoraSeguimiento
from .forms import BitacoraSeguimientoForm
from academico.models import Ficha
from usuarios.models import get_rol_nombre, es_administrador, es_coordinador, es_instructor, es_aprendiz


@login_required
def lista_seguimientos(request):
    """
    Historial general de bitácoras de visitas técnicas y acompañamiento.
    Filtrado por rol: Aprendices no tienen acceso. Instructores solo ven sus propias bitácoras.
    """
    if es_aprendiz(request.user):
        return HttpResponseForbidden('Los aprendices no tienen acceso al módulo de seguimiento.')

    ficha_id = request.GET.get('ficha', '').strip()
    seguimientos = BitacoraSeguimiento.objects.select_related('ficha', 'ficha__institucion', 'instructor', 'matricula__aprendiz').all()

    # Instructores solo ven sus propias bitácoras
    if es_instructor(request.user):
        seguimientos = seguimientos.filter(instructor=request.user)

    if ficha_id:
        seguimientos = seguimientos.filter(ficha_id=ficha_id)

    fichas = Ficha.objects.all().order_by('codigo_ficha')
    if es_instructor(request.user):
        fichas = fichas.filter(instructor_lider=request.user)

    context = {
        'seguimientos': seguimientos,
        'fichas': fichas,
        'ficha_seleccionada': ficha_id,
    }
    return render(request, 'seguimiento/lista.html', context)


@login_required
def nuevo_seguimiento(request):
    """
    Registro de una nueva bitácora de seguimiento con adjunto y validación RN-006.
    Solo Admin, Coordinador e Instructor SENA pueden registrar.
    """
    if es_aprendiz(request.user):
        return HttpResponseForbidden('Los aprendices no tienen acceso a este módulo.')

    ficha_param = request.GET.get('ficha', None)

    # Instructor: si viene con ficha, verificar que sea suya
    if es_instructor(request.user) and ficha_param:
        ficha = Ficha.objects.filter(pk=ficha_param, instructor_lider=request.user).first()
        if not ficha:
            return HttpResponseForbidden('No tiene permisos para registrar seguimiento en esta ficha.')

    if request.method == 'POST':
        form = BitacoraSeguimientoForm(request.POST, request.FILES)
        if form.is_valid():
            bitacora = form.save(commit=False)
            bitacora.instructor = request.user
            bitacora.save()
            messages.success(request, f"Bitácora de seguimiento del {bitacora.fecha_visita} guardada exitosamente.")
            return redirect('seguimiento_detalle', pk=bitacora.pk)
        else:
            messages.error(request, "Por favor revise los campos del formulario. Si registró compromisos, debe indicar fecha límite (RN-006).")
    else:
        form = BitacoraSeguimientoForm(ficha_id=ficha_param)

    return render(request, 'seguimiento/formulario.html', {'form': form, 'titulo': 'Registrar Bitácora de Visita / Seguimiento'})


@login_required
def detalle_seguimiento(request, pk):
    """
    Vista detallada de una bitácora de seguimiento, compromisos y acta adjunta.
    """
    if es_aprendiz(request.user):
        return HttpResponseForbidden('Los aprendices no tienen acceso a este módulo.')

    bitacora = get_object_or_404(BitacoraSeguimiento.objects.select_related('ficha', 'ficha__institucion', 'instructor', 'matricula__aprendiz'), pk=pk)

    # Instructores solo pueden ver sus propias bitácoras
    if es_instructor(request.user) and bitacora.instructor_id != request.user.id:
        return HttpResponseForbidden('No tiene permisos para consultar esta bitácora.')

    return render(request, 'seguimiento/detalle.html', {'bitacora': bitacora})
