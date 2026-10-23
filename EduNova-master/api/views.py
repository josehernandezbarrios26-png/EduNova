"""
EduNova - Vistas de la API REST
Endpoints JSON para consumo externo (app móvil, integraciones, reportes).

Autenticación: sesión Django o Basic Auth.
Todos los endpoints requieren usuario autenticado.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q

from academico.models import Ficha, Matricula
from instituciones.models import InstitucionEducativa
from evaluaciones.models import JuicioEvaluativo
from seguimiento.models import BitacoraSeguimiento

from .serializers import (
    FichaListSerializer,
    FichaDetalleSerializer,
    MatriculaSerializer,
    JuicioEvaluativoSerializer,
    InstitucionEducativaSerializer,
    BitacoraResumenSerializer,
)


class FichasListAPIView(APIView):
    """
    GET /api/fichas/
    Lista todas las fichas con filtros opcionales:
      ?estado=En+Ejecucion
      ?institucion=<id>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fichas = Ficha.objects.select_related(
            'programa', 'institucion', 'instructor_lider'
        ).all()

        estado = request.GET.get('estado')
        institucion_id = request.GET.get('institucion')

        if estado:
            fichas = fichas.filter(estado=estado)
        if institucion_id:
            fichas = fichas.filter(institucion_id=institucion_id)

        serializer = FichaListSerializer(fichas, many=True)
        return Response({
            'count': fichas.count(),
            'results': serializer.data,
        })


class FichaDetalleAPIView(APIView):
    """
    GET /api/fichas/<pk>/
    Detalle completo de una ficha con programa, institución y RAPs.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        ficha = get_object_or_404(
            Ficha.objects.select_related('programa', 'institucion', 'instructor_lider'),
            pk=pk
        )
        serializer = FichaDetalleSerializer(ficha)
        return Response(serializer.data)


class AprendicesFichaAPIView(APIView):
    """
    GET /api/fichas/<pk>/aprendices/
    Lista de aprendices matriculados en una ficha.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        ficha = get_object_or_404(Ficha, pk=pk)
        matriculas = Matricula.objects.filter(ficha=ficha).select_related(
            'aprendiz', 'aprendiz__perfil'
        ).order_by('aprendiz__last_name')

        serializer = MatriculaSerializer(matriculas, many=True)
        return Response({
            'ficha': ficha.codigo_ficha,
            'total': matriculas.count(),
            'aprendices': serializer.data,
        })


class CalificacionesFichaAPIView(APIView):
    """
    GET /api/fichas/<pk>/calificaciones/
    Juicios evaluativos de todos los aprendices de una ficha.
    Filtro opcional: ?rap=<id>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        ficha = get_object_or_404(Ficha, pk=pk)
        juicios = JuicioEvaluativo.objects.filter(
            matricula__ficha=ficha
        ).select_related(
            'matricula__aprendiz',
            'resultado_aprendizaje__competencia',
            'instructor',
        )

        rap_id = request.GET.get('rap')
        if rap_id:
            juicios = juicios.filter(resultado_aprendizaje_id=rap_id)

        serializer = JuicioEvaluativoSerializer(juicios, many=True)
        return Response({
            'ficha': ficha.codigo_ficha,
            'periodo_cerrado': ficha.periodo_cerrado,
            'total': juicios.count(),
            'calificaciones': serializer.data,
        })


class InstitucionesAPIView(APIView):
    """
    GET /api/instituciones/
    Directorio de instituciones educativas activas.
    Filtro opcional: ?municipio=<nombre>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        instituciones = InstitucionEducativa.objects.filter(activa=True)

        municipio = request.GET.get('municipio')
        if municipio:
            instituciones = instituciones.filter(municipio__icontains=municipio)

        serializer = InstitucionEducativaSerializer(instituciones, many=True)
        return Response({
            'count': instituciones.count(),
            'results': serializer.data,
        })


class ResumenDashboardAPIView(APIView):
    """
    GET /api/dashboard/
    Métricas generales del sistema: totales y tasas de aprobación.
    Útil para dashboards externos o apps móviles.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_colegios = InstitucionEducativa.objects.filter(activa=True).count()
        total_fichas = Ficha.objects.filter(estado='En Ejecucion').count()
        total_aprendices = Matricula.objects.filter(estado_formacion='En Formacion').count()

        total_aprobados = JuicioEvaluativo.objects.filter(juicio_valor='A').count()
        total_no_aprobados = JuicioEvaluativo.objects.filter(juicio_valor='D').count()
        total_evaluaciones = total_aprobados + total_no_aprobados
        porcentaje_aprobacion = round(
            (total_aprobados / total_evaluaciones * 100), 1
        ) if total_evaluaciones > 0 else 0

        fichas_por_municipio = list(
            Ficha.objects.filter(estado='En Ejecucion')
            .values('institucion__municipio')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        return Response({
            'total_colegios': total_colegios,
            'total_fichas_activas': total_fichas,
            'total_aprendices_activos': total_aprendices,
            'total_aprobados': total_aprobados,
            'total_no_aprobados': total_no_aprobados,
            'porcentaje_aprobacion': porcentaje_aprobacion,
            'fichas_por_municipio': fichas_por_municipio,
        })


class BitacorasAPIView(APIView):
    """
    GET /api/seguimientos/
    Listado de bitácoras de seguimiento.
    Filtros opcionales: ?ficha=<id>  ?tipo=<tipo>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bitacoras = BitacoraSeguimiento.objects.select_related(
            'ficha', 'ficha__institucion', 'instructor'
        ).order_by('-fecha_visita')

        ficha_id = request.GET.get('ficha')
        tipo = request.GET.get('tipo')

        if ficha_id:
            bitacoras = bitacoras.filter(ficha_id=ficha_id)
        if tipo:
            bitacoras = bitacoras.filter(tipo_seguimiento__icontains=tipo)

        serializer = BitacoraResumenSerializer(bitacoras[:50], many=True)
        return Response({
            'count': bitacoras.count(),
            'results': serializer.data,
        })
