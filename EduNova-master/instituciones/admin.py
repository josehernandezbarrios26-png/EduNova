from django.contrib import admin
from .models import InstitucionEducativa


@admin.register(InstitucionEducativa)
class InstitucionEducativaAdmin(admin.ModelAdmin):
    list_display = ('codigo_dane', 'nombre', 'municipio', 'rector_nombre', 'enlace_nombre', 'enlace_telefono', 'activa')
    list_filter = ('activa', 'municipio')
    search_fields = ('codigo_dane', 'nombre', 'municipio', 'rector_nombre', 'enlace_nombre')
    ordering = ('municipio', 'nombre')
    list_per_page = 20
