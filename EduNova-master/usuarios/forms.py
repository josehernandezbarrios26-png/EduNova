from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import PerfilUsuario, Rol
from instituciones.models import InstitucionEducativa


class LoginForm(AuthenticationForm):
    """
    Formulario de autenticación directo con usuario y contraseña.
    """
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingrese su usuario o documento',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingrese su contraseña',
        })
    )


class CambiarRolForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ('rol', 'institucion')
        labels = {
            'rol': 'Rol institucional',
            'institucion': 'Institución asociada',
        }
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'institucion': forms.Select(attrs={'class': 'form-select'}),
        }


class CrearUsuarioForm(forms.Form):
    """
    Formulario para crear un nuevo usuario con su perfil institucional.
    Valida RN-001 (documento único) y asigna rol desde el registro.
    """
    TIPO_DOC_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('TI', 'Tarjeta de Identidad'),
        ('CE', 'Cédula de Extranjería'),
        ('PEP', 'Permiso Especial de Permanencia'),
        ('PPT', 'Permiso por Protección Temporal'),
    ]

    # Datos de cuenta
    username = forms.CharField(
        max_length=150,
        label="Nombre de usuario",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'usuario_unico'}),
    )
    password = forms.CharField(
        label="Contraseña inicial",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña segura'}),
    )
    # Datos personales
    first_name = forms.CharField(
        max_length=150,
        label="Nombres",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres completos'}),
    )
    last_name = forms.CharField(
        max_length=150,
        label="Apellidos",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos completos'}),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
    )
    # Datos institucionales
    tipo_documento = forms.ChoiceField(
        choices=TIPO_DOC_CHOICES,
        label="Tipo de documento",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    numero_documento = forms.CharField(
        max_length=20,
        label="Número de documento",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número único (RN-001)'}),
    )
    telefono = forms.CharField(
        max_length=20,
        required=False,
        label="Teléfono",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Celular o teléfono (opcional)'}),
    )
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.all().order_by('nombre'),
        label="Rol institucional",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Seleccione un rol...",
    )
    institucion = forms.ModelChoiceField(
        queryset=InstitucionEducativa.objects.all().order_by('nombre'),
        label="Institución asociada",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Sin institución (opcional)",
        required=False,
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ya existe un usuario con este nombre de usuario.")
        return username

    def clean_numero_documento(self):
        num_doc = self.cleaned_data['numero_documento'].strip()
        if PerfilUsuario.objects.filter(numero_documento=num_doc).exists():
            raise forms.ValidationError("Ya existe un usuario con este número de documento (RN-001).")
        return num_doc


class EditarUsuarioForm(forms.ModelForm):
    """
    Formulario para editar datos de un usuario existente.
    No permite ver ni modificar contraseñas.
    """
    first_name = forms.CharField(
        max_length=150,
        label="Nombres",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        max_length=150,
        label="Apellidos",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = PerfilUsuario
        fields = ('rol', 'institucion', 'tipo_documento', 'numero_documento', 'telefono', 'esta_activo')
        labels = {
            'rol': 'Rol institucional',
            'institucion': 'Institución asociada',
            'tipo_documento': 'Tipo de documento',
            'numero_documento': 'Número de documento',
            'telefono': 'Teléfono',
            'esta_activo': '¿Cuenta activa?',
        }
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'institucion': forms.Select(attrs={'class': 'form-select'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'esta_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
