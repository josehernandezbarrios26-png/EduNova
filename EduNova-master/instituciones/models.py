"""
Aplicación: instituciones
Modelo: InstitucionEducativa
Reglas de Negocio: Código DANE único, directorio de colegios articulados en el Magdalena
"""

from django.db import models


class InstitucionEducativa(models.Model):
    """
    Representa una Institución Educativa (colegio) del Departamento del Magdalena
    que mantiene convenio de articulación con el Centro de Logística y Promoción Ecoturística.
    """
    ESTADOS_CONVENIO = [
        ('Vigente', 'Vigente'),
        ('Suspendido', 'Suspendido'),
        ('Por renovar', 'Por renovar'),
    ]

    codigo_dane = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código DANE Oficial",
        help_text="Código único asignado por el DANE / MEN al colegio."
    )
    nit = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="NIT",
        help_text="Número de identificación tributaria del colegio."
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre Oficial de la Institución Educativa"
    )
    municipio = models.CharField(
        max_length=100,
        verbose_name="Municipio del Magdalena",
        help_text="Municipio donde está ubicada la sede principal."
    )
    direccion = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Dirección Física"
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono Institucional"
    )
    rector_nombre = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Nombre del Rector(a)"
    )
    enlace_nombre = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Nombre del Docente Enlace / Coordinador"
    )
    enlace_telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono del Docente Enlace"
    )
    estado_convenio = models.CharField(
        max_length=20,
        choices=ESTADOS_CONVENIO,
        default='Vigente',
        verbose_name="Estado del Convenio"
    )
    activa = models.BooleanField(
        default=True,
        verbose_name="¿Convenio Activo y Vigente?"
    )
    fecha_renovacion = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha de Renovación del Convenio"
    )
    documento_convenio = models.FileField(
        upload_to='convenios/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Documento del Convenio"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro en EduNova"
    )

    class Meta:
        verbose_name = "Institución Educativa"
        verbose_name_plural = "Instituciones Educativas"
        ordering = ['municipio', 'nombre']

    @property
    def fichas_activas(self):
        from academico.models import Ficha
        return Ficha.objects.filter(institucion=self, estado__in=['En Ejecucion', 'Activa', 'En cierre'])

    @property
    def aprendices_totales(self):
        from academico.models import Matricula
        return Matricula.objects.filter(ficha__institucion=self).count()

    @property
    def instructor_asignado(self):
        from academico.models import Ficha
        ficha = Ficha.objects.filter(institucion=self).order_by('-fecha_inicio').first()
        return ficha.instructor_lider if ficha else None

    def __str__(self):
        return f"{self.nombre} ({self.municipio} - DANE: {self.codigo_dane})"
