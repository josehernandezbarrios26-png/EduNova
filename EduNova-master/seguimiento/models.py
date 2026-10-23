"""
Aplicación: seguimiento
Modelo: BitacoraSeguimiento
Reglas de Negocio Asociadas: RN-005 (Restricción por Ficha Asignada), RN-006 (Compromisos Obligatorios)
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from academico.models import Ficha, Matricula


class BitacoraSeguimiento(models.Model):
    """
    Registro formal de visitas presenciales o virtuales a las Instituciones Educativas,
    donde el instructor SENA documenta el avance, dificultades y compromisos de la Media Técnica.
    """
    TIPO_SEGUIMIENTO_CHOICES = [
        ('Presencial Aula', 'Visita Presencial en Aula de Clase'),
        ('Revision Taller', 'Revisión Presencial de Ambientes / Taller'),
        ('Reunion Colegio', 'Reunión con Rectoría / Docente Enlace'),
        ('Virtual', 'Sesión de Acompañamiento Virtual'),
        ('Comite', 'Comité de Seguimiento Formativo'),
    ]

    ficha = models.ForeignKey(
        Ficha,
        on_delete=models.CASCADE,
        related_name='seguimientos',
        verbose_name="Ficha de Media Técnica",
        help_text="Ficha técnica a la cual se realizó el acompañamiento."
    )
    matricula = models.ForeignKey(
        Matricula,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seguimientos_individuales',
        verbose_name="Aprendiz Específico (Opcional)",
        help_text="Dejar vacío si el seguimiento fue general para todo el grupo de la ficha."
    )
    instructor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='seguimientos_registrados',
        verbose_name="Instructor que Realizó la Visita"
    )
    fecha_visita = models.DateField(
        verbose_name="Fecha de la Visita o Sesión"
    )
    tipo_seguimiento = models.CharField(
        max_length=30,
        choices=TIPO_SEGUIMIENTO_CHOICES,
        default='Presencial Aula',
        verbose_name="Tipo de Seguimiento"
    )
    observaciones = models.TextField(
        verbose_name="Diagnóstico y Observaciones Pedagógicas / Técnicas"
    )
    # RN-006: Exigencia de compromisos y fecha de verificación
    compromisos = models.TextField(
        blank=True,
        null=True,
        verbose_name="Compromisos y Plan de Acción Acordado"
    )
    fecha_verificacion = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha Límite para Verificar Cumplimiento de Compromisos"
    )
    archivo_adjunto = models.FileField(
        upload_to='actas_seguimiento/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Acta de Visita Firmada o Soporte Escaneado (PDF/Imagen)"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Marca de Tiempo del Registro (Inmutable)"
    )

    class Meta:
        verbose_name = "Bitácora de Seguimiento"
        verbose_name_plural = "Bitácoras de Seguimiento"
        ordering = ['-fecha_visita', '-fecha_registro']

    def __str__(self):
        destino = self.matricula.aprendiz.get_full_name() if self.matricula else f"Grupo Ficha {self.ficha.codigo_ficha}"
        return f"Seguimiento {self.fecha_visita} - {destino} ({self.tipo_seguimiento})"

    def clean(self):
        """
        Validación de la regla RN-006:
        Si se registran compromisos, debe especificarse una fecha de verificación de los mismos.
        """
        super().clean()
        if self.compromisos and not self.fecha_verificacion:
            raise ValidationError({
                'fecha_verificacion': "Si se establecen compromisos de mejora, es obligatorio indicar una fecha de verificación (RN-006)."
            })
