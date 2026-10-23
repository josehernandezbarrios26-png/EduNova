from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from instituciones.models import InstitucionEducativa
from academico.models import ProgramaFormacion, Ficha, Matricula
from .models import BitacoraSeguimiento


class SeguimientoModelTest(TestCase):
    def setUp(self):
        self.colegio = InstitucionEducativa.objects.create(
            codigo_dane="147001000999",
            nombre="I.E. Simón Bolívar",
            municipio="Santa Marta"
        )
        self.programa = ProgramaFormacion.objects.create(
            codigo_programa="228106",
            denominacion="Técnico en Sistemas"
        )
        self.instructor = User.objects.create_user(
            username="inst_andrea",
            first_name="Andrea",
            last_name="Gómez"
        )
        self.ficha = Ficha.objects.create(
            codigo_ficha="2501890",
            programa=self.programa,
            institucion=self.colegio,
            instructor_lider=self.instructor,
            fecha_inicio="2026-02-01",
            fecha_fin="2027-11-30"
        )

    def test_bitacora_grupal_sin_novedades(self):
        """Verifica el guardado de una bitácora grupal estándar"""
        bitacora = BitacoraSeguimiento.objects.create(
            ficha=self.ficha,
            instructor=self.instructor,
            fecha_visita="2026-09-14",
            tipo_seguimiento="Presencial Aula",
            observaciones="Sesión formativa sin novedades. Excelente avance en algoritmos."
        )
        self.assertIsNotNone(bitacora.id)
        self.assertIsNone(bitacora.matricula)

    def test_regla_rn006_compromisos_exigen_fecha_verificacion(self):
        """Verifica la regla RN-006: Si hay compromisos, debe existir fecha de verificación"""
        bitacora = BitacoraSeguimiento(
            ficha=self.ficha,
            instructor=self.instructor,
            fecha_visita="2026-09-14",
            tipo_seguimiento="Presencial Aula",
            observaciones="Bajo rendimiento en el taller de redes.",
            compromisos="Presentar taller de recuperación.",
            fecha_verificacion=None  # Falta la fecha obligatoria
        )
        with self.assertRaises(ValidationError):
            bitacora.full_clean()
