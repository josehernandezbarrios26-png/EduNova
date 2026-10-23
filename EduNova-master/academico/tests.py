from django.test import TestCase
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from instituciones.models import InstitucionEducativa
from .models import Asistencia, ProgramaFormacion, Competencia, ResultadoAprendizaje, Ficha, Matricula


class AcademicoModelTest(TestCase):
    def setUp(self):
        self.colegio = InstitucionEducativa.objects.create(
            codigo_dane="147001000123",
            nombre="I.E. Técnica Departamental de Ciénaga",
            municipio="Ciénaga"
        )
        self.programa = ProgramaFormacion.objects.create(
            codigo_programa="228106",
            denominacion="Técnico en Sistemas",
            version="102"
        )
        self.instructor = User.objects.create_user(
            username="instructor_carlos",
            first_name="Carlos",
            last_name="Martínez"
        )
        self.ficha = Ficha.objects.create(
            codigo_ficha="2501234",
            programa=self.programa,
            institucion=self.colegio,
            instructor_lider=self.instructor,
            fecha_inicio="2026-02-01",
            fecha_fin="2027-11-30"
        )
        self.aprendiz = User.objects.create_user(
            username="aprendiz_juan",
            first_name="Juan",
            last_name="Pérez"
        )

    def test_creacion_ficha_y_matricula_valida(self):
        """Verifica la vinculación de un aprendiz a una ficha en grado 10° (RN-007)"""
        matricula = Matricula.objects.create(
            ficha=self.ficha,
            aprendiz=self.aprendiz,
            grado_escolar="10"
        )
        self.assertEqual(matricula.ficha.codigo_ficha, "2501234")
        self.assertEqual(matricula.estado_formacion, "En Formacion")
        self.assertEqual(matricula.grado_escolar, "10")

    def test_regla_rn002_no_duplicar_matricula_en_misma_ficha(self):
        """Verifica que un aprendiz no pueda matricularse dos veces en la misma ficha (RN-002)"""
        Matricula.objects.create(
            ficha=self.ficha,
            aprendiz=self.aprendiz,
            grado_escolar="10"
        )
        # Intentar matricular al mismo aprendiz nuevamente en la misma ficha
        with self.assertRaises(IntegrityError):
            Matricula.objects.create(
                ficha=self.ficha,
                aprendiz=self.aprendiz,
                grado_escolar="10"
            )

    def test_asistencia_aprobada_o_desaprobada_y_unica_por_fecha(self):
        matricula = Matricula.objects.create(
            ficha=self.ficha,
            aprendiz=self.aprendiz,
            grado_escolar="10"
        )
        asistencia = Asistencia.objects.create(
            matricula=matricula,
            fecha="2026-09-16",
            estado="Aprobada",
            registrado_por=self.instructor,
        )

        self.assertEqual(asistencia.get_estado_display(), "Aprobada")
        asistencia.estado = "Desaprobada"
        asistencia.save()
        self.assertEqual(Asistencia.objects.get(pk=asistencia.pk).estado, "Desaprobada")

        with self.assertRaises(IntegrityError):
            Asistencia.objects.create(
                matricula=matricula,
                fecha="2026-09-16",
                estado="Aprobada",
                registrado_por=self.instructor,
            )
