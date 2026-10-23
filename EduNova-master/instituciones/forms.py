from django import forms
from .models import InstitucionEducativa


class InstitucionEducativaForm(forms.ModelForm):
    """
    Formulario para registrar o editar Instituciones Educativas en convenio.
    """
    class Meta:
        model = InstitucionEducativa
        fields = [
            'codigo_dane', 'nit', 'nombre', 'municipio', 'direccion',
            'telefono', 'rector_nombre', 'enlace_nombre', 'enlace_telefono',
            'estado_convenio', 'fecha_renovacion', 'documento_convenio', 'activa'
        ]
        widgets = {
            'codigo_dane': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 147001000123'}),
            'nit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 900123456-7'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo del colegio'}),
            'municipio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Santa Marta, Ciénaga, Aracataca'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección física de la sede principal'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono fijo o celular'}),
            'rector_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del rector(a)'}),
            'enlace_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del docente enlace'}),
            'enlace_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono del docente enlace'}),
            'estado_convenio': forms.Select(attrs={'class': 'form-select'}),
            'fecha_renovacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'documento_convenio': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
