"""
EduNova - Serializers para la API REST
Convierte los modelos Django a JSON y viceversa.
"""

from rest_framework import serializers
from academico.models import ProgramaFormacion, Ficha, Matricula, Competencia, ResultadoAprendizaje
from instituciones.models import InstitucionEducativa
from evaluaciones.models import JuicioEvaluativo
from seguimiento.models import BitacoraSeguimiento
from django.contrib.auth.models import User


class InstitucionEducativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitucionEducativa
        fields = ['id', 'codigo_dane', 'nombre', 'municipio', 'rector_nombre',
                  'enlace_nombre', 'activa', 'fecha_registro']


class ProgramaFormacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramaFormacion
        fields = ['id', 'codigo_programa', 'denominacion', 'version', 'activo']


class ResultadoAprendizajeSerializer(serializers.ModelSerializer):
    competencia_codigo = serializers.CharField(source='competencia.codigo', read_only=True)

    class Meta:
        model = ResultadoAprendizaje
        fields = ['id', 'codigo', 'descripcion', 'competencia_codigo']


class FichaListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados."""
    programa_nombre = serializers.CharField(source='programa.denominacion', read_only=True)
    institucion_nombre = serializers.CharField(source='institucion.nombre', read_only=True)
    municipio = serializers.CharField(source='institucion.municipio', read_only=True)
    instructor_nombre = serializers.SerializerMethodField()
    total_aprendices = serializers.SerializerMethodField()

    class Meta:
        model = Ficha
        fields = [
            'id', 'codigo_ficha', 'programa_nombre', 'institucion_nombre',
            'municipio', 'instructor_nombre', 'fecha_inicio', 'fecha_fin',
            'estado', 'periodo_cerrado', 'total_aprendices',
        ]

    def get_instructor_nombre(self, obj):
        return obj.instructor_lider.get_full_name() or obj.instructor_lider.username

    def get_total_aprendices(self, obj):
        return obj.matriculas.filter(estado_formacion='En Formacion').count()


class FichaDetalleSerializer(serializers.ModelSerializer):
    """Serializer completo con relaciones para detalle."""
    programa = ProgramaFormacionSerializer(read_only=True)
    institucion = InstitucionEducativaSerializer(read_only=True)
    instructor_nombre = serializers.SerializerMethodField()
    total_aprendices = serializers.SerializerMethodField()
    resultados_aprendizaje = serializers.SerializerMethodField()

    class Meta:
        model = Ficha
        fields = [
            'id', 'codigo_ficha', 'programa', 'institucion',
            'instructor_nombre', 'fecha_inicio', 'fecha_fin',
            'estado', 'periodo_cerrado', 'total_aprendices',
            'resultados_aprendizaje',
        ]

    def get_instructor_nombre(self, obj):
        return obj.instructor_lider.get_full_name() or obj.instructor_lider.username

    def get_total_aprendices(self, obj):
        return obj.matriculas.filter(estado_formacion='En Formacion').count()

    def get_resultados_aprendizaje(self, obj):
        raps = ResultadoAprendizaje.objects.filter(
            competencia__programa=obj.programa
        ).select_related('competencia')
        return ResultadoAprendizajeSerializer(raps, many=True).data


class MatriculaSerializer(serializers.ModelSerializer):
    aprendiz_nombre = serializers.SerializerMethodField()
    aprendiz_documento = serializers.SerializerMethodField()
    ficha_codigo = serializers.CharField(source='ficha.codigo_ficha', read_only=True)

    class Meta:
        model = Matricula
        fields = [
            'id', 'ficha_codigo', 'aprendiz_nombre', 'aprendiz_documento',
            'grado_escolar', 'estado_formacion', 'fecha_matricula',
            'acudiente_nombre', 'acudiente_telefono',
        ]

    def get_aprendiz_nombre(self, obj):
        return obj.aprendiz.get_full_name() or obj.aprendiz.username

    def get_aprendiz_documento(self, obj):
        try:
            return obj.aprendiz.perfil.numero_documento
        except Exception:
            return ''


class JuicioEvaluativoSerializer(serializers.ModelSerializer):
    aprendiz_nombre = serializers.SerializerMethodField()
    rap_codigo = serializers.CharField(source='resultado_aprendizaje.codigo', read_only=True)
    rap_descripcion = serializers.CharField(source='resultado_aprendizaje.descripcion', read_only=True)
    instructor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = JuicioEvaluativo
        fields = [
            'id', 'aprendiz_nombre', 'rap_codigo', 'rap_descripcion',
            'instructor_nombre', 'juicio_valor', 'observaciones',
            'fecha_evaluacion', 'fecha_registro',
        ]

    def get_aprendiz_nombre(self, obj):
        return obj.matricula.aprendiz.get_full_name() or obj.matricula.aprendiz.username

    def get_instructor_nombre(self, obj):
        return obj.instructor.get_full_name() or obj.instructor.username


class BitacoraResumenSerializer(serializers.ModelSerializer):
    instructor_nombre = serializers.SerializerMethodField()
    ficha_codigo = serializers.CharField(source='ficha.codigo_ficha', read_only=True)
    institucion_nombre = serializers.CharField(source='ficha.institucion.nombre', read_only=True)

    class Meta:
        model = BitacoraSeguimiento
        fields = [
            'id', 'ficha_codigo', 'institucion_nombre', 'instructor_nombre',
            'fecha_visita', 'tipo_seguimiento', 'observaciones',
            'compromisos', 'fecha_verificacion', 'fecha_registro',
        ]

    def get_instructor_nombre(self, obj):
        return obj.instructor.get_full_name() or obj.instructor.username
