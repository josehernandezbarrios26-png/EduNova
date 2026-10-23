"""
EduNova - Módulo de Envío de Correos Electrónicos
Centraliza todas las notificaciones del sistema.

En desarrollo (EMAIL_BACKEND=console) los correos se imprimen en la terminal.
En producción cambia EMAIL_BACKEND a smtp en el .env.
"""

from django.core.mail import send_mail
from django.conf import settings


def notificar_cierre_periodo(ficha, usuario_coordinador):
    """
    Notifica al instructor líder cuando el Coordinador cierra
    o reabre el periodo evaluativo de su ficha.
    """
    instructor = ficha.instructor_lider
    if not instructor.email:
        return  # No tiene correo registrado, se omite silenciosamente

    estado = "CERRADO" if ficha.periodo_cerrado else "REABIERTO"
    icono  = "🔒" if ficha.periodo_cerrado else "🔓"

    asunto = f"[EduNova] Periodo evaluativo {estado} — Ficha {ficha.codigo_ficha}"

    mensaje = f"""
Estimado(a) {instructor.get_full_name() or instructor.username},

El Coordinador {usuario_coordinador.get_full_name() or usuario_coordinador.username} ha realizado
la siguiente acción en el sistema EduNova:

  {icono}  El periodo evaluativo de la Ficha {ficha.codigo_ficha} ha sido {estado}.

Detalles de la Ficha:
  • Código:      {ficha.codigo_ficha}
  • Programa:    {ficha.programa.denominacion}
  • Institución: {ficha.institucion.nombre} ({ficha.institucion.municipio})
  • Estado:      {ficha.get_estado_display()}

{"⚠️  A partir de este momento NO podrás registrar ni modificar calificaciones en esta ficha." if ficha.periodo_cerrado else "✅  Puedes volver a registrar y modificar calificaciones en esta ficha."}

Si tienes dudas, comunícate con la Coordinación de Articulación.

—
EduNova · Sistema de Integración Técnica Education
Centro de Logística y Promoción Ecoturística del Magdalena
Este es un mensaje automático, no respondas a este correo.
""".strip()

    send_mail(
        subject=asunto,
        message=mensaje,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[instructor.email],
        fail_silently=True,  # No rompe el flujo si el correo falla
    )


def enviar_constancia_matricula(matricula):
    """
    Envía al aprendiz (y al acudiente si tiene teléfono/correo) una
    constancia de que fue matriculado exitosamente en una ficha.
    """
    aprendiz = matricula.aprendiz
    if not aprendiz.email:
        return

    ficha = matricula.ficha

    asunto = f"[EduNova] Confirmación de Matrícula — Ficha {ficha.codigo_ficha}"

    mensaje = f"""
Estimado(a) {aprendiz.get_full_name() or aprendiz.username},

¡Bienvenido(a) al programa de Media Técnica SENA! Tu matrícula ha sido registrada exitosamente.

Datos de tu Matrícula:
  • Ficha:           {ficha.codigo_ficha}
  • Programa:        {ficha.programa.denominacion}
  • Institución:     {ficha.institucion.nombre} ({ficha.institucion.municipio})
  • Grado Escolar:   {matricula.get_grado_escolar_display()}
  • Estado:          {matricula.get_estado_formacion_display()}
  • Fecha Matrícula: {matricula.fecha_matricula.strftime('%d/%m/%Y')}

Tus datos de acceso al sistema EduNova:
  • Usuario:         {aprendiz.username}
  • Contraseña:      (la que te fue entregada por el instructor)

Puedes ingresar al sistema en: http://edunova.sena.edu.co/

—
EduNova · Sistema de Integración Técnica Education
Centro de Logística y Promoción Ecoturística del Magdalena
Este es un mensaje automático, no respondas a este correo.
""".strip()

    send_mail(
        subject=asunto,
        message=mensaje,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[aprendiz.email],
        fail_silently=True,
    )
