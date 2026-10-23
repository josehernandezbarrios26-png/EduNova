from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User

from instituciones.models import InstitucionEducativa
from academico.models import ProgramaFormacion, Ficha, Matricula
from seguimiento.models import BitacoraSeguimiento


class InstitucionConvenioTest(TestCase):
    def test_institucion_guarda_estado_convenio_y_documento_basico(self):
        institucion = InstitucionEducativa.objects.create(
            codigo_dane='12345678',
            nombre='Colegio SENA Demo',
            municipio='Santa Marta',
            nit='900123456-7',
            estado_convenio='Vigente',
        )

        self.assertEqual(institucion.nit, '900123456-7')
        self.assertEqual(institucion.estado_convenio, 'Vigente')
        self.assertTrue(institucion.fichas_activas.count() >= 0)

    def test_dashboard_presenta_alertas_de_seguimiento_y_fichas_por_vencer(self):
        institucion = InstitucionEducativa.objects.create(
            codigo_dane='87654321',
            nombre='Institución Con Riesgo',
            municipio='Ciénaga',
            nit='900987654-4',
            estado_convenio='Vigente',
        )
        programa = ProgramaFormacion.objects.create(
            codigo_programa='PRG-99',
            denominacion='Técnico en Servicios',
        )
        instructor = User.objects.create_user(username='instructor_alerta', password='Pass1234!')
        ficha = Ficha.objects.create(
            codigo_ficha='2824001',
            programa=programa,
            institucion=institucion,
            instructor_lider=instructor,
            fecha_inicio=timezone.now().date() - timedelta(days=200),
            fecha_fin=timezone.now().date() + timedelta(days=10),
            estado='En Ejecucion',
        )
        aprendiz = User.objects.create_user(username='aprendiz_alerta', password='Pass1234!')
        Matricula.objects.create(
            ficha=ficha,
            aprendiz=aprendiz,
            estado_formacion='En Formacion',
        )
        BitacoraSeguimiento.objects.create(
            ficha=ficha,
            instructor=instructor,
            fecha_visita=timezone.now().date() - timedelta(days=45),
            observaciones='Sin seguimiento reciente',
        )

        self.client.force_login(instructor)
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fichas por vencer')
        self.assertContains(response, 'Instituciones con alerta')
        self.assertContains(response, '2824001')
