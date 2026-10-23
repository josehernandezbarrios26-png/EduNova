"""
Matricula a los aprendices de prueba (aprendiz1-5) en la ficha DEMO-2026-01
y les asigna calificaciones y asistencias de ejemplo.

Ejecutar con:
    python manage.py shell -c "exec(open('matricular_aprendices.py', encoding='utf-8-sig').read())"
"""

from datetime import date
from django.contrib.auth.models import User
from django.utils import timezone
from academico.models import Ficha, Matricula, ResultadoAprendizaje, Asistencia
from evaluaciones.models import JuicioEvaluativo

ficha = Ficha.objects.get(codigo_ficha='DEMO-2026-01')
instructor = ficha.instructor_lider

aprendices_config = [
    ('aprendiz1', '10', 'A', 'A', None),   # nombre, grado, rap1, rap2, rap3
    ('aprendiz2', '10', 'D', 'A', 'A'),
    ('aprendiz3', '11', 'A', 'D', None),
    ('aprendiz4', '11', 'A', 'A', 'D'),
    ('aprendiz5', '10', 'D', 'A', 'A'),
]

raps = list(ResultadoAprendizaje.objects.filter(
    competencia__programa=ficha.programa
).order_by('codigo'))

matriculas = []
for username, grado, j1, j2, j3 in aprendices_config:
    user = User.objects.get(username=username)
    matricula, creada = Matricula.objects.get_or_create(
        ficha=ficha,
        aprendiz=user,
        defaults={
            'grado_escolar': grado,
            'estado_formacion': 'En Formacion',
            'acudiente_nombre': f'Acudiente de {user.first_name}',
            'acudiente_telefono': f'3005500{user.perfil.numero_documento[-3:]}',
        }
    )
    estado = 'Matriculado' if creada else 'Ya existía'
    print(f'  {username}: {estado} en ficha {ficha.codigo_ficha}')
    matriculas.append((matricula, j1, j2, j3))

# Asignar calificaciones
juicios_config = list(zip(
    [m for m, _, _, _ in matriculas],
    [j1 for _, j1, _, _ in matriculas],
    [j2 for _, _, j2, _ in matriculas],
    [j3 for _, _, _, j3 in matriculas],
))

obs_por_juicio = {
    'A': 'Cumple satisfactoriamente los criterios de desempeño del resultado de aprendizaje.',
    'D': 'Requiere refuerzo y plan de mejoramiento para alcanzar los criterios establecidos.',
}

total_juicios = 0
for matricula, j1, j2, j3 in juicios_config:
    for rap, juicio in zip(raps[:3], [j1, j2, j3]):
        if juicio is None:
            continue
        JuicioEvaluativo.objects.update_or_create(
            matricula=matricula,
            resultado_aprendizaje=rap,
            defaults={
                'instructor': instructor,
                'juicio_valor': juicio,
                'observaciones': obs_por_juicio[juicio],
                'fecha_evaluacion': timezone.localdate(),
            }
        )
        total_juicios += 1

print(f'  Juicios asignados: {total_juicios}')

# Registrar asistencias de ejemplo
asistencia_config = [
    ('aprendiz1', 'Aprobada'),
    ('aprendiz2', 'Aprobada'),
    ('aprendiz3', 'Desaprobada'),
    ('aprendiz4', 'Aprobada'),
    ('aprendiz5', 'Aprobada'),
]

fecha_asistencia = date(2026, 10, 20)
total_asistencias = 0
for username, estado in asistencia_config:
    user = User.objects.get(username=username)
    matricula = Matricula.objects.get(ficha=ficha, aprendiz=user)
    Asistencia.objects.get_or_create(
        matricula=matricula,
        fecha=fecha_asistencia,
        defaults={
            'estado': estado,
            'observacion': 'Registro de asistencia de ejemplo para demostración.',
            'registrado_por': instructor,
        }
    )
    total_asistencias += 1

print(f'  Asistencias registradas: {total_asistencias}')
print()
print('=== RESUMEN ===')
print(f'Ficha: {ficha.codigo_ficha} — {ficha.programa.denominacion}')
print(f'Total aprendices en ficha: {ficha.matriculas.count()}')
print(f'Total juicios en ficha: {JuicioEvaluativo.objects.filter(matricula__ficha=ficha).count()}')
print()
print('Boletines disponibles en: /evaluaciones/boletines/')
