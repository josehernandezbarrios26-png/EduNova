from django.test import TestCase
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import Client
from .models import Rol, PerfilUsuario


class UsuarioModelTest(TestCase):
    def setUp(self):
        self.rol_coordinador = Rol.objects.create(
            nombre="Coordinador",
            descripcion="Líder del proceso de articulación con la Media Técnica"
        )
        self.user = User.objects.create_user(
            username="coordinador1",
            email="coord@sena.edu.co",
            first_name="Carlos",
            last_name="Mendoza"
        )
        self.perfil = PerfilUsuario.objects.get(usuario=self.user)
        self.perfil.rol = self.rol_coordinador
        self.perfil.numero_documento = "1082999888"
        self.perfil.save()

    def test_creacion_perfil_correcta(self):
        """Verifica que el perfil se haya creado y asociado correctamente al rol"""
        self.assertEqual(self.perfil.rol.nombre, "Coordinador")
        self.assertEqual(self.perfil.numero_documento, "1082999888")
        self.assertTrue(self.perfil.esta_activo)

    def test_regla_rn001_unicidad_documento(self):
        """Verifica la regla RN-001: No pueden existir dos personas con el mismo número de documento"""
        otro_user = User.objects.create_user(
            username="instructor_dup",
            email="inst@sena.edu.co"
        )
        otro_perfil = PerfilUsuario.objects.get(usuario=otro_user)
        otro_perfil.numero_documento = "1082999888"  # Mismo número

        with self.assertRaises(IntegrityError):
            otro_perfil.save()


class GestionRolesTest(TestCase):
    def setUp(self):
        self.rol_admin = Rol.objects.create(nombre='Administrador')
        self.rol_estudiante = Rol.objects.create(nombre='Estudiante')
        self.admin = User.objects.create_user(username='admin_roles', password='ClaveSegura123')
        self.admin.perfil.rol = self.rol_admin
        self.admin.perfil.numero_documento = '1000000001'
        self.admin.perfil.save()
        self.usuario = User.objects.create_user(username='usuario', password='ClaveSegura123')
        self.usuario.perfil.rol = self.rol_estudiante
        self.usuario.perfil.numero_documento = '1000000002'
        self.usuario.perfil.save()
        self.client = Client()

    def test_administrador_puede_cambiar_cualquier_rol(self):
        self.client.login(username='admin_roles', password='ClaveSegura123')
        response = self.client.post('/usuarios/roles/', {
            'perfil_id': self.usuario.perfil.pk,
            'rol': self.rol_admin.pk,
        })

        self.assertRedirects(response, '/usuarios/roles/')
        self.usuario.perfil.refresh_from_db()
        self.assertEqual(self.usuario.perfil.rol, self.rol_admin)

    def test_usuario_no_administrador_no_puede_cambiar_roles(self):
        self.client.login(username='usuario', password='ClaveSegura123')
        response = self.client.get('/usuarios/roles/')

        self.assertEqual(response.status_code, 403)

    def test_dashboard_instructor_usa_espacio_funcional_del_rol(self):
        instructor = User.objects.create_user(username='instr_roles', password='ClaveSegura123')
        instructor.perfil.rol = Rol.objects.create(nombre='Instructor SENA')
        instructor.perfil.numero_documento = '1000000003'
        instructor.perfil.save()

        self.client.login(username='instr_roles', password='ClaveSegura123')
        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Espacio del Instructor')
        self.assertContains(response, 'Fichas asignadas')

    def test_docente_enlace_no_tiene_acceso_a_roles_globales(self):
        docente = User.objects.create_user(username='docente_roles', password='ClaveSegura123')
        docente.perfil.rol = Rol.objects.create(nombre='Docente Enlace')
        docente.perfil.numero_documento = '1000000004'
        docente.perfil.save()

        self.client.login(username='docente_roles', password='ClaveSegura123')
        response = self.client.get('/usuarios/roles/')

        self.assertEqual(response.status_code, 403)
