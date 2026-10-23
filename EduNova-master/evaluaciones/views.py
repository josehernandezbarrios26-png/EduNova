from io import BytesIO
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from .models import JuicioEvaluativo
from academico.models import Ficha, ResultadoAprendizaje, Matricula
from usuarios.models import get_rol_nombre
from edunova_project.correos import notificar_cierre_periodo


def _rol_nombre(user):
    return get_rol_nombre(user)


def _es_coordinador_o_admin(user):
    return user.is_superuser or _rol_nombre(user) in {'Administrador', 'Coordinador'}


def _matriculas_visibles(user):
    matriculas = Matricula.objects.select_related(
        'aprendiz', 'ficha', 'ficha__programa', 'ficha__institucion'
    )
    rol = _rol_nombre(user)
    if _es_coordinador_o_admin(user):
        return matriculas
    if rol == 'Instructor SENA':
        return matriculas.filter(ficha__instructor_lider=user)
    if rol == 'Docente Enlace':
        perfil = getattr(user, 'perfil', None)
        return matriculas.filter(ficha__institucion_id=perfil.institucion_id) if perfil and perfil.institucion_id else matriculas.none()
    if rol == 'Aprendiz':
        return matriculas.filter(aprendiz=user)
    return matriculas.none()


def _puede_ver_boletin(user, matricula):
    return _matriculas_visibles(user).filter(pk=matricula.pk).exists()


def _puede_calificar(user, ficha):
    rol = _rol_nombre(user)
    if _es_coordinador_o_admin(user):
        return True
    if rol == 'Instructor SENA':
        return ficha.instructor_lider_id == user.id
    return False


def _fichas_calificables(user):
    fichas = Ficha.objects.all().order_by('codigo_ficha')
    if _es_coordinador_o_admin(user):
        return fichas
    if _rol_nombre(user) == 'Instructor SENA':
        return fichas.filter(instructor_lider=user)
    if _rol_nombre(user) == 'Docente Enlace':
        perfil = getattr(user, 'perfil', None)
        return fichas.filter(institucion_id=perfil.institucion_id) if perfil and perfil.institucion_id else fichas.none()
    return fichas.none()


def _calcular_boletin(matricula):
    competencias = []
    total_raps = 0
    aprobados = 0
    no_aprobados = 0
    pendientes = 0
    juicios = {
        juicio.resultado_aprendizaje_id: juicio
        for juicio in JuicioEvaluativo.objects.filter(
            matricula=matricula,
            resultado_aprendizaje__competencia__programa=matricula.ficha.programa,
        )
    }
    for competencia in matricula.ficha.programa.competencias.select_related('programa').prefetch_related('resultados').all():
        raps = list(competencia.resultados.all())
        if not raps:
            continue
        resultados = []
        aprobados_competencia = 0
        evaluados_competencia = 0
        for rap in raps:
            total_raps += 1
            juicio = juicios.get(rap.id)
            estado = 'Sin evaluar'
            if juicio:
                evaluados_competencia += 1
                estado = 'Aprobado' if juicio.juicio_valor == 'A' else 'Por mejorar'
                if juicio.juicio_valor == 'A':
                    aprobados += 1
                    aprobados_competencia += 1
                else:
                    no_aprobados += 1
            else:
                pendientes += 1
            resultados.append({
                'id': rap.id,
                'codigo': rap.codigo,
                'descripcion': rap.descripcion,
                'juicio_valor': juicio.juicio_valor if juicio else '',
                'estado': estado,
                'observacion': juicio.observaciones if juicio else '',
            })
        competencias.append({
            'codigo': competencia.codigo,
            'descripcion': competencia.descripcion,
            'resultados': resultados,
            'aprobados': aprobados_competencia,
            'evaluados': evaluados_competencia,
        })
    evaluados = aprobados + no_aprobados
    return {
        'competencias': competencias,
        'total_raps': total_raps,
        'aprobados': aprobados,
        'no_aprobados': no_aprobados,
        'pendientes': pendientes,
        'evaluados': evaluados,
    }


@login_required
def boletines_lista(request):
    matriculas = _matriculas_visibles(request.user).order_by(
        'aprendiz__last_name', 'aprendiz__first_name'
    )
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        matriculas = matriculas.filter(
            Q(aprendiz__first_name__icontains=busqueda)
            | Q(aprendiz__last_name__icontains=busqueda)
            | Q(aprendiz__username__icontains=busqueda)
            | Q(ficha__codigo_ficha__icontains=busqueda)
        )
    return render(request, 'evaluaciones/boletines_lista.html', {
        'matriculas': matriculas,
        'busqueda': busqueda,
        'puede_calificar': _rol_nombre(request.user) in {'Administrador', 'Coordinador', 'Instructor SENA'} or request.user.is_superuser,
    })


@login_required
def boletin_aprendiz(request, matricula_id):
    matricula = get_object_or_404(_matriculas_visibles(request.user), pk=matricula_id)
    if not _puede_ver_boletin(request.user, matricula):
        return HttpResponseForbidden('No tiene permisos para consultar este boletín.')

    puede_calificar = _puede_calificar(request.user, matricula.ficha)
    if request.method == 'POST':
        if not puede_calificar:
            return HttpResponseForbidden('Su rol no puede calificar este boletín.')
        if matricula.ficha.periodo_cerrado:
            messages.error(request, 'El periodo evaluativo está cerrado. No se pueden modificar las notas.')
            return redirect('evaluaciones_boletin', matricula_id=matricula.pk)
        datos = _calcular_boletin(matricula)
        guardados = 0
        for competencia in datos['competencias']:
            for rap in competencia['resultados']:
                valor = request.POST.get(f"juicio_{rap['id']}", '').strip()
                if valor not in {'A', 'D'}:
                    continue
                JuicioEvaluativo.objects.update_or_create(
                    matricula=matricula,
                    resultado_aprendizaje_id=rap['id'],
                    defaults={
                        'instructor': request.user,
                        'juicio_valor': valor,
                        'observaciones': request.POST.get(f"obs_{rap['id']}", '').strip(),
                        'fecha_evaluacion': timezone.now().date(),
                    },
                )
                guardados += 1
        messages.success(request, f'Se guardaron {guardados} juicios evaluativos.')
        return redirect('evaluaciones_boletin', matricula_id=matricula.pk)

    datos = _calcular_boletin(matricula)
    context = {
        'matricula': matricula,
        'aprendiz': matricula.aprendiz,
        'ficha': matricula.ficha,
        'datos': datos,
        'puede_calificar': puede_calificar,
    }
    return render(request, 'evaluaciones/boletin.html', context)


@login_required
def boletin_exportar_pdf(request, matricula_id):
    matricula = get_object_or_404(_matriculas_visibles(request.user), pk=matricula_id)

    datos = _calcular_boletin(matricula)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f'Boletin-{matricula.aprendiz.username}')
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph('Boletín académico EduNova', styles['Title']))
    story.append(Paragraph(f'Aprendiz: {matricula.aprendiz.get_full_name() or matricula.aprendiz.username}', styles['Heading2']))
    story.append(Paragraph(f'Ficha: {matricula.ficha.codigo_ficha} | Programa: {matricula.ficha.programa.denominacion}', styles['BodyText']))
    story.append(Spacer(1, 12))

    table_data = [['Competencia', 'RAP', 'Juicio', 'Estado', 'Observación']]
    for competencia in datos['competencias']:
        for rap in competencia['resultados']:
            table_data.append([
                competencia['codigo'],
                rap['codigo'],
                rap['juicio_valor'] or '-',
                rap['estado'],
                (rap['observacion'] or '-')[:80],
            ])
    table = Table(table_data, colWidths=[100, 65, 45, 75, 200])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6D28D9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="boletin_{matricula.aprendiz.username}.pdf"'
    return response


@login_required
def boletin_exportar_xlsx(request, matricula_id):
    matricula = get_object_or_404(_matriculas_visibles(request.user), pk=matricula_id)

    datos = _calcular_boletin(matricula)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Boletin'
    ws.append(['Boletín académico EduNova'])
    ws.append(['Aprendiz', matricula.aprendiz.get_full_name() or matricula.aprendiz.username])
    ws.append(['Ficha', matricula.ficha.codigo_ficha])
    ws.append(['Programa', matricula.ficha.programa.denominacion])
    ws.append([])
    ws.append(['Competencia', 'RAP', 'Juicio', 'Estado', 'Observación'])

    for competencia in datos['competencias']:
        for rap in competencia['resultados']:
            ws.append([
                competencia['codigo'],
                rap['codigo'],
                rap['juicio_valor'] or '',
                rap['estado'],
                rap['observacion'] or '',
            ])

    buffer = BytesIO()
    wb.save(buffer)
    response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="boletin_{matricula.aprendiz.username}.xlsx"'
    return response


@login_required
def sabana_calificaciones(request):
    """
    Sábana interactiva de evaluación masiva de Resultados de Aprendizaje (RAP).
    Permite al instructor seleccionar Ficha y RAP, y asentar juicios 'A' o 'D'
    para toda la lista de aprendices. Valida las reglas RN-003 y RN-004.
    """
    ficha_id = request.GET.get('ficha', None)
    rap_id = request.GET.get('rap', None)

    fichas = _fichas_calificables(request.user)
    ficha_actual = None
    rap_actual = None
    aprendices_datos = []

    if ficha_id:
        ficha_actual = get_object_or_404(fichas, pk=ficha_id)
        # Obtener RAPs del programa de la ficha
        raps = ResultadoAprendizaje.objects.filter(competencia__programa=ficha_actual.programa).select_related('competencia')
    else:
        raps = ResultadoAprendizaje.objects.none()

    if ficha_actual and rap_id:
        if not _puede_calificar(request.user, ficha_actual):
            return HttpResponseForbidden('Su rol no puede calificar esta ficha.')
        rap_actual = get_object_or_404(raps, pk=rap_id)

        # Procesar guardado masivo de calificaciones
        if request.method == 'POST':
            # RN-004: Verificar si el periodo está cerrado
            if ficha_actual.periodo_cerrado:
                messages.error(request, "Acción Denegada (RN-004): El periodo de esta ficha se encuentra cerrado. No se pueden modificar calificaciones.")
                return redirect(f"/evaluaciones/?ficha={ficha_id}&rap={rap_id}")

            matriculas = ficha_actual.matriculas.select_related('aprendiz').all()
            guardados = 0

            for mat in matriculas:
                juicio_key = f"juicio_{mat.id}"
                obs_key = f"obs_{mat.id}"
                juicio_valor = request.POST.get(juicio_key, '').strip()
                observacion = request.POST.get(obs_key, '').strip()

                if juicio_valor in ['A', 'D']:  # RN-003
                    JuicioEvaluativo.objects.update_or_create(
                        matricula=mat,
                        resultado_aprendizaje=rap_actual,
                        defaults={
                            'instructor': request.user,
                            'juicio_valor': juicio_valor,
                            'observaciones': observacion,
                            'fecha_evaluacion': timezone.now().date(),
                        }
                    )
                    guardados += 1

            messages.success(request, f"Se asentaron exitosamente {guardados} juicios evaluativos para el resultado {rap_actual.codigo}.")
            return redirect(f"/evaluaciones/?ficha={ficha_id}&rap={rap_id}")

        # Cargar aprendices y sus calificaciones existentes si las hay
        matriculas = ficha_actual.matriculas.select_related('aprendiz', 'aprendiz__perfil').order_by('aprendiz__last_name')
        juicios_existentes = {
            j.matricula_id: j for j in JuicioEvaluativo.objects.filter(
                matricula__in=matriculas,
                resultado_aprendizaje=rap_actual
            )
        }

        for mat in matriculas:
            juicio_obj = juicios_existentes.get(mat.id)
            aprendices_datos.append({
                'matricula': mat,
                'juicio_actual': juicio_obj.juicio_valor if juicio_obj else '',
                'observacion_actual': juicio_obj.observaciones if juicio_obj else '',
            })

    context = {
        'fichas': fichas,
        'ficha_actual': ficha_actual,
        'raps': raps,
        'rap_actual': rap_actual,
        'aprendices_datos': aprendices_datos,
    }
    return render(request, 'evaluaciones/calificar.html', context)


@login_required
def cerrar_periodo_ficha(request, ficha_id):
    """
    Cierre formal del periodo evaluativo de una ficha (RN-004).
    Solo para coordinadores o administradores.
    """
    ficha = get_object_or_404(Ficha, pk=ficha_id)
    if request.method == 'POST':
        ficha.periodo_cerrado = not ficha.periodo_cerrado
        ficha.save()
        estado_texto = "CERRADO" if ficha.periodo_cerrado else "REABIERTO"
        messages.info(request, f"El periodo evaluativo de la Ficha {ficha.codigo_ficha} ahora se encuentra {estado_texto}.")
        # Notificar al instructor líder por correo
        notificar_cierre_periodo(ficha, request.user)
        return redirect('fichas_detalle', pk=ficha.pk)

    return redirect('fichas_detalle', pk=ficha.pk)
