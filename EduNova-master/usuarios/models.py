"""
Aplicación: usuarios
Modelos: Rol, PerfilUsuario
Reglas de Negocio Asociadas: RN-001 (Unicidad de Documento), RN-008 (Borrado Lógico)
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from instituciones.models import InstitucionEducativa


ROLES_OFICIALES = {
    'Administrador',
    'Coordinador',
    'Instructor SENA',
    'Docente Enlace',
    'Aprendiz',
}

ROL_ALIASES = {
    'Docente I.E.': 'Docente Enlace',
    'Estudiante': 'Aprendiz',
    'Alumno': 'Aprendiz',
    'Profesor': 'Docente Enlace',
}


def normalizar_rol_nombre(nombre):
    if not nombre:
        return ''
    nombre = str(nombre).strip()
    return ROL_ALIASES.get(nombre, nombre)


def get_rol_nombre(user):
    perfil = getattr(user, 'perfil', None)
    rol = getattr(perfil, 'rol', None)
    if rol and rol.nombre:
        return normalizar_rol_nombre(rol.nombre)
    return ''


def tiene_rol(user, *roles):
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    nombre = get_rol_nombre(user)
    return nombre in {normalizar_rol_nombre(rol) for rol in roles}


def es_administrador(user):
    return bool(user and (getattr(user, 'is_superuser', False) or tiene_rol(user, 'Administrador')))


def es_coordinador(user):
    return tiene_rol(user, 'Coordinador')


def es_instructor(user):
    return tiene_rol(user, 'Instructor SENA')


def es_docente_enlace(user):
    return tiene_rol(user, 'Docente Enlace')


def es_aprendiz(user):
    return tiene_rol(user, 'Aprendiz')


class Rol(models.Model):
    """
    Representa los perfiles de seguridad institucional en EduNova.
    Ejemplos: Administrador, Coordinador, Instructor SENA, Docente Enlace, Aprendiz.
    """
    nombre = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nombre del Rol"
    )
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Descripción de Funciones"
    )

    class Meta:
        verbose_name = "Rol de Usuario"
        verbose_name_plural = "Roles de Usuario"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    """
    Extensión del usuario estándar de Django para almacenar datos institucionales,
    documento de identidad y rol asignado en la Media Técnica.
    Roles oficiales: Administrador, Coordinador, Instructor SENA,
    Docente Enlace y Aprendiz.
    """
    TIPO_DOC_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('TI', 'Tarjeta de Identidad'),
        ('CE', 'Cédula de Extranjería'),
        ('PEP', 'Permiso Especial de Permanencia'),
        ('PPT', 'Permiso por Protección Temporal'),
    ]

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name="Cuenta de Usuario"
    )
    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        related_name='usuarios',
        verbose_name="Rol Institucional",
        null=True,
        blank=True
    )
    institucion = models.ForeignKey(
        InstitucionEducativa,
        on_delete=models.SET_NULL,
        related_name='perfiles_enlace',
        verbose_name="Institución Educativa",
        null=True,
        blank=True,
        help_text="Institución asociada al usuario, especialmente para Docentes Enlace."
    )
    tipo_documento = models.CharField(
        max_length=5,
        choices=TIPO_DOC_CHOICES,
        default='CC',
        verbose_name="Tipo de Documento"
    )
    # RN-001: No pueden existir dos personas con el mismo número de documento
    numero_documento = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de Documento"
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono de Contacto"
    )
    # RN-008: Borrado lógico / estado de la cuenta
    esta_activo = models.BooleanField(
        default=True,
        verbose_name="¿Cuenta Activa?"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"
        ordering = ['usuario__last_name', 'usuario__first_name']

    def __str__(self):
        nombre_completo = self.usuario.get_full_name() or self.usuario.username
        rol_nombre = self.rol.nombre if self.rol else "Sin Rol"
        return f"{nombre_completo} ({rol_nombre} - {self.numero_documento})"


@receiver(post_save, sender=User)
def crear_o_actualizar_perfil_usuario(sender, instance, created, **kwargs):
    """
    Señal automática para asegurar que cada Usuario de Django tenga su Perfil correspondiente.
    """
    if created:
        PerfilUsuario.objects.get_or_create(
            usuario=instance,
            defaults={'numero_documento': f"DOC-{instance.id}-{instance.username[:10]}"}
        )
