from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from instituciones.models import InstitucionEducativa
from academico.models import ProgramaFormacion, Competencia, ResultadoAprendizaje, Ficha, Matricula
from usuarios.models import Rol
from .models import JuicioEvaluativo


class EvaluacionesModelTest(TestCase):
    def setUp(self):
        self.colegio = InstitucionEducativa.objects.create(
            codigo_dane="147001000777",
            nombre="I.E. Agropecuaria",
            municipio="Aracataca"
        )
        self.programa = ProgramaFormacion.objects.create(
            codigo_programa="228106",
            denominacion="Técnico en Sistemas"
        )
        self.competencia = Competencia.objects.create(
            programa=self.programa,
            codigo="220501001",
            descripcion="Mantenimiento Preventivo y Correctivo de Equipos"
        )
        self.rap = ResultadoAprendizaje.objects.create(
            competencia=self.competencia,
            codigo="RAP-01",
            descripcion="Desensamblar y ensamblar equipos de cómputo de acuerdo con el manual."
        )
        self.instructor = User.objects.create_user(
            username="inst_roberto",
            first_name="Roberto",
            last_name="Peña"
        )
        self.rol_instructor = Rol.objects.create(nombre='Instructor SENA')
        self.instructor.perfil.rol = self.rol_instructor
        self.instructor.perfil.save()
        self.ficha = Ficha.objects.create(
            codigo_ficha="2501452",
            programa=self.programa,
            institucion=self.colegio,
            instructor_lider=self.instructor,
            fecha_inicio="2026-02-01",
            fecha_fin="2027-11-30",
            periodo_cerrado=False
        )
        self.aprendiz = User.objects.create_user(
            username="aprendiz_camila",
            first_name="Camila",
            last_name="Ortiz"
        )
        self.rol_aprendiz = Rol.objects.create(nombre='Aprendiz')
        self.aprendiz.perfil.rol = self.rol_aprendiz
        self.aprendiz.perfil.save()
        self.matricula = Matricula.objects.create(
            ficha=self.ficha,
            aprendiz=self.aprendiz,
            grado_escolar="10"
        )

    def test_regla_rn003_juicio_aprobado_valido(self):
        """Verifica la asignación de un juicio válido ('A')"""
        juicio = JuicioEvaluativo(
            matricula=self.matricula,
            resultado_aprendizaje=self.rap,
            instructor=self.instructor,
            juicio_valor='A',
            fecha_evaluacion="2026-09-14"
        )
        juicio.full_clean()
        juicio.save()
        self.assertEqual(juicio.juicio_valor, 'A')

    def test_regla_rn003_rechazar_juicio_invalido(self):
        """Verifica la regla RN-003: Rechaza juicios no válidos distintos de 'A' o 'D'"""
        juicio = JuicioEvaluativo(
            matricula=self.matricula,
            resultado_aprendizaje=self.rap,
            instructor=self.instructor,
            juicio_valor='B',  # Valor no permitido
            fecha_evaluacion="2026-09-14"
        )
        with self.assertRaises(ValidationError):
            juicio.full_clean()

    def test_regla_rn004_bloqueo_por_periodo_cerrado(self):
        """Verifica la regla RN-004: Impide evaluar si la ficha tiene su periodo formalmente cerrado"""
        self.ficha.periodo_cerrado = True
        self.ficha.save()

        juicio = JuicioEvaluativo(
            matricula=self.matricula,
            resultado_aprendizaje=self.rap,
            instructor=self.instructor,
            juicio_valor='A',
            fecha_evaluacion="2026-09-14"
        )
        with self.assertRaises(ValidationError):
            juicio.full_clean()

    def test_vista_boletin_retorna_200(self):
        """Debe permitir consultar el boletín del aprendiz en la ficha asignada."""
        self.client.force_login(self.instructor)
        url = reverse('evaluaciones_boletin', args=[self.matricula.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Boletín')

    def test_exportacion_excel_del_boletin(self):
        """Debe generar un archivo Excel del boletín con contenido válido."""
        self.client.force_login(self.instructor)
        url = reverse('evaluaciones_boletin_xlsx', args=[self.matricula.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', response['Content-Type'])

    def test_sabana_calificaciones_se_renderiza(self):
        """La sábana debe abrir con una ficha y un resultado de aprendizaje válidos."""
        self.client.force_login(self.instructor)
        url = f"{reverse('evaluaciones_calificar')}?ficha={self.ficha.id}&rap={self.rap.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Boletín')
        self.assertContains(response, self.aprendiz.first_name)

    def test_sabana_guarda_juicio_del_aprendiz(self):
        """La sábana debe registrar el juicio enviado para el aprendiz matriculado."""
        self.client.force_login(self.instructor)
        url = f"{reverse('evaluaciones_calificar')}?ficha={self.ficha.id}&rap={self.rap.id}"
        response = self.client.post(url, {f'juicio_{self.matricula.id}': 'A', f'obs_{self.matricula.id}': 'Buen trabajo'})
        self.assertEqual(response.status_code, 302)
        juicio = JuicioEvaluativo.objects.get(matricula=self.matricula, resultado_aprendizaje=self.rap)
        self.assertEqual(juicio.juicio_valor, 'A')

    def test_aprendiz_solo_ve_su_boletin(self):
        otro_aprendiz = User.objects.create_user(username='aprendiz_otro', first_name='Otro')
        otro_aprendiz.perfil.rol = self.rol_aprendiz
        otro_aprendiz.perfil.save()
        otra_matricula = Matricula.objects.create(ficha=self.ficha, aprendiz=otro_aprendiz)

        self.client.force_login(self.aprendiz)
        lista = self.client.get(reverse('evaluaciones_boletines'))
        self.assertEqual(lista.status_code, 200)
        self.assertContains(lista, 'Camila')
        self.assertNotContains(lista, 'Otro')
        self.assertEqual(self.client.get(reverse('evaluaciones_boletin', args=[otra_matricula.id])).status_code, 404)

    def test_docente_enlace_ve_solo_su_institucion(self):
        otra_institucion = InstitucionEducativa.objects.create(
            codigo_dane='147001000888', nombre='I.E. Otra', municipio='Santa Marta'
        )
        otra_ficha = Ficha.objects.create(
            codigo_ficha='2501453', programa=self.programa, institucion=otra_institucion,
            instructor_lider=self.instructor, fecha_inicio='2026-02-01', fecha_fin='2027-11-30'
        )
        otro_aprendiz = User.objects.create_user(username='aprendiz_otro', first_name='Otro')
        Matricula.objects.create(ficha=otra_ficha, aprendiz=otro_aprendiz)
        enlace = User.objects.create_user(username='docente_enlace', first_name='Docente')
        enlace.perfil.rol = Rol.objects.create(nombre='Docente Enlace')
        enlace.perfil.institucion = self.colegio
        enlace.perfil.save()

        self.client.force_login(enlace)
        response = self.client.get(reverse('evaluaciones_boletines'))
        self.assertContains(response, 'Camila')
        self.assertNotContains(response, 'Otro')
        own_bulletin = self.client.post(reverse('evaluaciones_boletin', args=[self.matricula.id]), {
            f'juicio_{self.rap.id}': 'A'
        })
        self.assertEqual(own_bulletin.status_code, 403)
        self.assertEqual(
            self.client.post(reverse('evaluaciones_boletin', args=[otra_ficha.matriculas.get().id]), {
                f'juicio_{self.rap.id}': 'D'
            }).status_code,
            404,
        )

    def test_docente_enlace_no_puede_agregar_nota(self):
        docente = User.objects.create_user(username='docente_enlace_2', first_name='Miguel')
        docente.perfil.rol = Rol.objects.create(nombre='Docente Enlace')
        docente.perfil.institucion = self.colegio
        docente.perfil.save()

        self.client.force_login(docente)
        response = self.client.post(reverse('evaluaciones_boletin', args=[self.matricula.id]), {
            f'juicio_{self.rap.id}': 'A', f'obs_{self.rap.id}': 'No debería permitirlo.'
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(JuicioEvaluativo.objects.filter(matricula=self.matricula, resultado_aprendizaje=self.rap).exists())

    def test_coordinador_puede_calificar_boletin(self):
        coordinador = User.objects.create_user(username='coord_pruebas')
        coordinador.perfil.rol = Rol.objects.create(nombre='Coordinador')
        coordinador.perfil.save()
        otra_institucion = InstitucionEducativa.objects.create(
            codigo_dane='147001000999', nombre='I.E. Coordinación', municipio='Ciénaga'
        )
        otra_ficha = Ficha.objects.create(
            codigo_ficha='2501454', programa=self.programa, institucion=otra_institucion,
            instructor_lider=self.instructor, fecha_inicio='2026-02-01', fecha_fin='2027-11-30'
        )
        otro_aprendiz = User.objects.create_user(username='aprendiz_coord', first_name='Laura')
        Matricula.objects.create(ficha=otra_ficha, aprendiz=otro_aprendiz)

        self.client.force_login(coordinador)
        lista = self.client.get(reverse('evaluaciones_boletines'))
        self.assertContains(lista, 'Laura')
        response = self.client.post(reverse('evaluaciones_boletin', args=[self.matricula.id]), {
            f'juicio_{self.rap.id}': 'D', f'obs_{self.rap.id}': 'Requiere reforzar el resultado.'
        })
        self.assertEqual(response.status_code, 302)
        juicio = JuicioEvaluativo.objects.get(matricula=self.matricula, resultado_aprendizaje=self.rap)
        self.assertEqual(juicio.juicio_valor, 'D')

    def test_instructor_puede_calificar_boletin_de_su_ficha(self):
        self.client.force_login(self.instructor)
        response = self.client.post(reverse('evaluaciones_boletin', args=[self.matricula.id]), {
            f'juicio_{self.rap.id}': 'A', f'obs_{self.rap.id}': 'Alcanzó el resultado.'
        })
        self.assertEqual(response.status_code, 302)
        juicio = JuicioEvaluativo.objects.get(matricula=self.matricula, resultado_aprendizaje=self.rap)
        self.assertEqual(juicio.juicio_valor, 'A')

    def test_no_se_puede_calificar_con_periodo_cerrado(self):
        self.ficha.periodo_cerrado = True
        self.ficha.save()
        self.client.force_login(self.instructor)
        response = self.client.post(reverse('evaluaciones_boletin', args=[self.matricula.id]), {
            f'juicio_{self.rap.id}': 'A'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(JuicioEvaluativo.objects.filter(matricula=self.matricula).exists())

    def test_instructor_no_puede_calificar_ficha_ajena(self):
        otro_instructor = User.objects.create_user(username='otro_instructor')
        otra_ficha = Ficha.objects.create(
            codigo_ficha='2501453', programa=self.programa, institucion=self.colegio,
            instructor_lider=otro_instructor, fecha_inicio='2026-02-01', fecha_fin='2027-11-30'
        )
        otro_aprendiz = User.objects.create_user(username='aprendiz_otro')
        otra_matricula = Matricula.objects.create(ficha=otra_ficha, aprendiz=otro_aprendiz)

        self.client.force_login(self.instructor)
        response = self.client.post(reverse('evaluaciones_boletin', args=[otra_matricula.id]), {
            f'juicio_{self.rap.id}': 'A'
        })
        self.assertEqual(response.status_code, 404)
