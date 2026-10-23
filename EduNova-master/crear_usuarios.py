"""
Script de Datos Iniciales - EduNova
Crea los roles y usuarios del sistema para el equipo de trabajo y pruebas.

Ejecutar con:
    python manage.py shell < crear_usuarios.py
"""

import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edunova_project.settings')

from django.contrib.auth.models import User
from usuarios.models import Rol, PerfilUsuario

print("=" * 60)
print("  EduNova - Creación de Roles y Usuarios")
print("=" * 60)

# ──────────────────────────────────────────────
# 1. ROLES
# ──────────────────────────────────────────────
roles_data = [
    {
        'nombre': 'Administrador',
        'descripcion': 'Acceso total al sistema. Gestiona usuarios, instituciones, fichas y configuración general.'
    },
    {
        'nombre': 'Coordinador',
        'descripcion': 'Supervisa fichas, cierra periodos evaluativos, genera reportes y gestiona instructores.'
    },
    {
        'nombre': 'Instructor SENA',
        'descripcion': 'Registra seguimientos, asienta juicios evaluativos y gestiona aprendices de sus fichas.'
    },
    {
        'nombre': 'Docente Enlace',
        'descripcion': 'Docente del colegio articulado. Consulta información de la ficha de su institución.'
    },
    {
        'nombre': 'Aprendiz',
        'descripcion': 'Estudiante de grado 10° u 11° matriculado en un programa de Media Técnica SENA.'
    },
]

roles_creados = {}
for r in roles_data:
    rol, creado = Rol.objects.get_or_create(
        nombre=r['nombre'],
        defaults={'descripcion': r['descripcion']}
    )
    roles_creados[r['nombre']] = rol
    estado = "✔ Creado" if creado else "→ Ya existe"
    print(f"  Rol [{estado}]: {rol.nombre}")

print()

# ──────────────────────────────────────────────
# 2. USUARIOS
# ──────────────────────────────────────────────
usuarios_data = [
    # ── ADMINISTRADOR ──
    {
        'username':   'admin_edunova',
        'password':   'Admin@2026*',
        'first_name': 'Administrador',
        'last_name':  'EduNova',
        'email':      'admin@edunova.edu.co',
        'is_staff':   True,
        'is_superuser': True,
        'rol':        'Administrador',
        'tipo_doc':   'CC',
        'num_doc':    '1000000001',
        'telefono':   '3001000001',
    },
    # ── COORDINADOR ──
    {
        'username':   'coordinador',
        'password':   'Coord@2026*',
        'first_name': 'Carlos',
        'last_name':  'Martínez Roa',
        'email':      'coordinador@edunova.edu.co',
        'is_staff':   True,
        'is_superuser': False,
        'rol':        'Coordinador',
        'tipo_doc':   'CC',
        'num_doc':    '1000000002',
        'telefono':   '3001000002',
    },
    # ── INSTRUCTORES SENA ──
    {
        'username':   'instructor1',
        'password':   'Inst@2026*',
        'first_name': 'Ana',
        'last_name':  'Pérez López',
        'email':      'ana.perez@edunova.edu.co',
        'is_staff':   False,
        'is_superuser': False,
        'rol':        'Instructor SENA',
        'tipo_doc':   'CC',
        'num_doc':    '1000000003',
        'telefono':   '3001000003',
    },
    {
        'username':   'instructor2',
        'password':   'Inst@2026*',
        'first_name': 'Luis',
        'last_name':  'González Torres',
        'email':      'luis.gonzalez@edunova.edu.co',
        'is_staff':   False,
        'is_superuser': False,
        'rol':        'Instructor SENA',
        'tipo_doc':   'CC',
        'num_doc':    '1000000004',
        'telefono':   '3001000004',
    },
    {
        'username':   'instructor3',
        'password':   'Inst@2026*',
        'first_name': 'María',
        'last_name':  'Rodríguez Campo',
        'email':      'maria.rodriguez@edunova.edu.co',
        'is_staff':   False,
        'is_superuser': False,
        'rol':        'Instructor SENA',
        'tipo_doc':   'CC',
        'num_doc':    '1000000005',
        'telefono':   '3001000005',
    },
    # ── DOCENTES ENLACE ──
    {
        'username':   'docente_enlace1',
        'password':   'Docente@2026*',
        'first_name': 'Rosa',
        'last_name':  'Fuentes Díaz',
        'email':      'rosa.fuentes@ie.edu.co',
        'is_staff':   False,
        'is_superuser': False,
        'rol':        'Docente Enlace',
        'tipo_doc':   'CC',
        'num_doc':    '1000000006',
        'telefono':   '3001000006',
    },
    {
        'username':   'docente_enlace2',
        'password':   'Docente@2026*',
        'first_name': 'Pedro',
        'last_name':  'Herrera Blanco',
        'email':      'pedro.herrera@ie.edu.co',
        'is_staff':   False,
        'is_superuser': False,
        'rol':        'Docente Enlace',
        'tipo_doc':   'CC',
        'num_doc':    '1000000007',
        'telefono':   '3001000007',
    },
    # ── APRENDICES ──
    {
        'username':   'aprendiz1',
        'password':   'Aprendiz@2026*',
        'first_name': 'Santiago',
        'last_name':  'Morales Vega',
        'email':      'santiago.morales@aprendiz.edu.co',
        'is_staff':   False,
        'is_superuser': False,
        'rol':        'Aprendiz',
        'tipo_doc':   'TI',
        'num_doc':    '1000100001',
        'telefono':   '3011000001',
    },
    {
        'username':   'aprendiz2',
        'password':   'Aprendiz@2026*',
        'first_name': 'Valentina',
        'last_name':  'Castro Niño',
        'email':      'valentina.castro@aprendiz.edu.co',
        'is_staff':   False,
        'is_superuser': False,
        'rol':        'Aprendiz',
        'tipo_doc':   'TI',
        'num_doc':    '1000100002',
        'telefono':   '3011000002',
    },
    {
        'username':   'aprendiz3',
        'password':   'Aprendiz@2026*',
        'first_name': 'Camilo',
        'last_name':  'Suárez Ríos',
        'email':      'camilo.suarez@aprendiz.edu.co',
        'is_staff':   False,
        'is_superuser': False,
        'rol':        'Aprendiz',
        'tipo_doc':   'TI',
        'num_doc':    '1000100003',
        'telefono':   '3011000003',
    },
    {
        'username':   'aprendiz4',
        'password':   'Aprendiz@2026*',
        'first_name': 'Luisa',
        'last_name':  'Mendoza Parra',
        'email':      'luisa.mendoza@aprendiz.edu.co',
        'is_staff':   False,
        'is_superuser': False,
        'rol':        'Aprendiz',
        'tipo_doc':   'TI',
        'num_doc':    '1000100004',
        'telefono':   '3011000004',
    },
    {
        'username':   'aprendiz5',
        'password':   'Aprendiz@2026*',
        'first_name': 'Julián',
        'last_name':  'Ospina Leal',
        'email':      'julian.ospina@aprendiz.edu.co',
        'is_staff':   False,
        'is_superuser': False,
        'rol':        'Aprendiz',
        'tipo_doc':   'TI',
        'num_doc':    '1000100005',
        'telefono':   '3011000005',
    },
]

print("  Creando usuarios...")
print()

for u in usuarios_data:
    user, creado = User.objects.get_or_create(
        username=u['username'],
        defaults={
            'first_name':   u['first_name'],
            'last_name':    u['last_name'],
            'email':        u['email'],
            'is_staff':     u['is_staff'],
            'is_superuser': u['is_superuser'],
        }
    )

    if creado:
        user.set_password(u['password'])
        user.save()

    # Actualizar o crear el perfil
    perfil, _ = PerfilUsuario.objects.update_or_create(
        usuario=user,
        defaults={
            'rol':              roles_creados[u['rol']],
            'tipo_documento':   u['tipo_doc'],
            'numero_documento': u['num_doc'],
            'telefono':         u['telefono'],
            'esta_activo':      True,
        }
    )

    estado = "✔ Creado" if creado else "→ Ya existe"
    print(f"  [{estado}] {u['first_name']} {u['last_name']}")
    print(f"           Usuario: {u['username']:20s}  Contraseña: {u['password']}")
    print(f"           Rol: {u['rol']:20s}  Doc: {u['num_doc']}")
    print()

print("=" * 60)
print("  ¡Usuarios creados exitosamente!")
print()
print("  RESUMEN DE ACCESOS:")
print(f"  {'ROL':<20} {'USUARIO':<20} {'CONTRASEÑA'}")
print(f"  {'-'*60}")
for u in usuarios_data:
    print(f"  {u['rol']:<20} {u['username']:<20} {u['password']}")
print("=" * 60)
