"""Crea datos academicos ficticios para probar el flujo de calificaciones.

Ejecutar desde la carpeta del proyecto con:
    python manage.py shell -c "exec(open('crear_datos_demo.py', encoding='utf-8-sig').read())"
"""

from datetime import date

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from academico.models import Asistencia, Competencia, Ficha, Matricula, ProgramaFormacion, ResultadoAprendizaje
from evaluaciones.models import JuicioEvaluativo
from instituciones.models import InstitucionEducativa
from seguimiento.models import BitacoraSeguimiento
from usuarios.models import PerfilUsuario, Rol


with transaction.atomic():
    instructor = User.objects.get(username='instructor1')
    rol_aprendiz = Rol.objects.get(nombre='Aprendiz')

    institucion, _ = InstitucionEducativa.objects.update_or_create(
        codigo_dane='DEMO-DANE-001',
        defaults={
            'nombre': 'Institucion Educativa Demo EduNova',
            'municipio': 'Santa Marta',
            'direccion': 'Sede ficticia para demostracion',
            'rector_nombre': 'Rector de demostracion',
            'enlace_nombre': 'Docente de demostracion',
            'estado_convenio': 'Vigente',
            'activa': True,
        },
    )

    programa, _ = ProgramaFormacion.objects.update_or_create(
        codigo_programa='DEMO-SW-2026',
        defaults={
            'denominacion': 'Tecnico en Programacion de Software (Demo)',
            'version': '1',
            'activo': True,
        },
    )

    competencia, _ = Competencia.objects.update_or_create(
        programa=programa,
        codigo='DEMO-COMP-01',
        defaults={
            'descripcion': 'Desarrollar soluciones de software aplicando fundamentos de programacion.',
        },
    )

    raps = [
        ('DEMO-RAP-01', 'Identificar requisitos y necesidades de una solucion de software.'),
        ('DEMO-RAP-02', 'Construir algoritmos usando variables, decisiones y ciclos.'),
        ('DEMO-RAP-03', 'Probar el funcionamiento de una solucion y documentar resultados.'),
    ]
    resultados = []
    for codigo, descripcion in raps:
        resultado, _ = ResultadoAprendizaje.objects.update_or_create(
            competencia=competencia,
            codigo=codigo,
            defaults={'descripcion': descripcion},
        )
        resultados.append(resultado)

    ficha, _ = Ficha.objects.update_or_create(
        codigo_ficha='DEMO-2026-01',
        defaults={
            'programa': programa,
            'institucion': institucion,
            'instructor_lider': instructor,
            'fecha_inicio': date(2026, 1, 26),
            'fecha_fin': date(2026, 11, 30),
            'estado': 'En Ejecucion',
            'periodo_cerrado': False,
        },
    )

    aprendices = [
        ('demo_aprendiz01', 'Laura', 'Mendoza', '10', 'DEMO-10001'),
        ('demo_aprendiz02', 'Andres', 'Pineda', '10', 'DEMO-10002'),
        ('demo_aprendiz03', 'Camila', 'Torres', '10', 'DEMO-10003'),
        ('demo_aprendiz04', 'Mateo', 'Castro', '11', 'DEMO-10004'),
        ('demo_aprendiz05', 'Valeria', 'Rojas', '11', 'DEMO-10005'),
    ]

    matriculas = {}
    for username, first_name, last_name, grado, documento in aprendices:
        user, creado = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': f'{username}@demo.edunova.local',
                'is_active': True,
            },
        )
        if creado:
            user.set_unusable_password()
            user.save(update_fields=['password'])

        PerfilUsuario.objects.update_or_create(
            usuario=user,
            defaults={
                'rol': rol_aprendiz,
                'tipo_documento': 'TI',
                'numero_documento': documento,
                'esta_activo': True,
            },
        )
        matricula, _ = Matricula.objects.update_or_create(
            ficha=ficha,
            aprendiz=user,
            defaults={
                'grado_escolar': grado,
                'estado_formacion': 'En Formacion',
                'acudiente_nombre': f'Acudiente de {first_name}',
                'acudiente_telefono': f'30055500{documento[-2:]}',
            },
        )

        matriculas[username] = matricula

    resultados_por_codigo = {resultado.codigo: resultado for resultado in resultados}
    calificaciones_demo = [
        ('demo_aprendiz01', 'DEMO-RAP-01', 'A', 'Identifica los requisitos con claridad.'),
        ('demo_aprendiz02', 'DEMO-RAP-01', 'D', 'Reforzar el levantamiento de requisitos.'),
        ('demo_aprendiz03', 'DEMO-RAP-01', 'A', 'Relaciona las necesidades con la solucion.'),
        ('demo_aprendiz04', 'DEMO-RAP-01', 'A', 'Presenta un analisis completo.'),
        ('demo_aprendiz05', 'DEMO-RAP-01', 'D', 'Completar la entrevista y validar los datos.'),
        ('demo_aprendiz01', 'DEMO-RAP-02', 'A', 'Construye algoritmos ordenados y legibles.'),
        ('demo_aprendiz02', 'DEMO-RAP-02', 'A', 'Aplica correctamente decisiones y ciclos.'),
        ('demo_aprendiz03', 'DEMO-RAP-02', 'D', 'Practicar ciclos y probar casos limite.'),
    ]
    for username, rap_codigo, juicio, observacion in calificaciones_demo:
        JuicioEvaluativo.objects.update_or_create(
            matricula=matriculas[username],
            resultado_aprendizaje=resultados_por_codigo[rap_codigo],
            defaults={
                'instructor': instructor,
                'juicio_valor': juicio,
                'observaciones': observacion,
                'fecha_evaluacion': timezone.localdate(),
            },
        )

    seguimientos_demo = [
        {
            'fecha_visita': date(2026, 9, 18),
            'tipo_seguimiento': 'Presencial Aula',
            'observaciones': 'Seguimiento grupal de fundamentos de programacion. Se evidencia avance en el analisis de requisitos.',
            'compromisos': '',
            'fecha_verificacion': None,
        },
        {
            'fecha_visita': date(2026, 9, 29),
            'tipo_seguimiento': 'Virtual',
            'observaciones': 'Se revisaron ejercicios de algoritmos y se identifico la necesidad de reforzar ciclos.',
            'compromisos': 'Entregar ejercicios de practica de ciclos y pruebas de escritorio.',
            'fecha_verificacion': date(2026, 10, 12),
        },
    ]
    for seguimiento in seguimientos_demo:
        fecha_visita = seguimiento.pop('fecha_visita')
        tipo_seguimiento = seguimiento.pop('tipo_seguimiento')
        BitacoraSeguimiento.objects.update_or_create(
            ficha=ficha,
            instructor=instructor,
            fecha_visita=fecha_visita,
            tipo_seguimiento=tipo_seguimiento,
            defaults=seguimiento,
        )

    asistencias_demo = [
        ('demo_aprendiz01', 'Aprobada', 'Asistencia registrada para la sesion de algoritmos.'),
        ('demo_aprendiz02', 'Desaprobada', 'Inasistencia registrada; requiere seguimiento.'),
        ('demo_aprendiz03', 'Aprobada', 'Participacion completa en la sesion.'),
        ('demo_aprendiz04', 'Aprobada', 'Asistencia registrada para la sesion de algoritmos.'),
        ('demo_aprendiz05', 'Desaprobada', 'Inasistencia justificada pendiente de confirmar.'),
    ]
    for username, estado, observacion in asistencias_demo:
        Asistencia.objects.update_or_create(
            matricula=matriculas[username],
            fecha=date(2026, 9, 29),
            defaults={
                'estado': estado,
                'observacion': observacion,
                'registrado_por': instructor,
            },
        )

print(f'Institucion: {institucion.nombre}')
print(f'Programa: {programa.denominacion}')
print(f'Ficha: {ficha.codigo_ficha} | Instructor: {instructor.username}')
print(f'Aprendices matriculados: {ficha.matriculas.count()}')
print(f'RAP disponibles para calificar: {len(resultados)}')
print(f'Juicios de ejemplo: {JuicioEvaluativo.objects.filter(matricula__ficha=ficha).count()}')
print(f'Seguimientos de ejemplo: {BitacoraSeguimiento.objects.filter(ficha=ficha).count()}')
print(f'Registros de asistencia: {Asistencia.objects.filter(matricula__ficha=ficha).count()}')
print(f'URL con notas A/D: /evaluaciones/?ficha={ficha.pk}&rap={resultados[0].pk}')
print(f'URL para practicar el RAP pendiente: /evaluaciones/?ficha={ficha.pk}&rap={resultados[2].pk}')
