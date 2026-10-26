#!/usr/bin/env bash
set -e

echo "==> Ejecutando migraciones de base de datos..."
python manage.py migrate --no-input

echo "==> Verificando si existen usuarios..."
python -c "
import os, sys, django
INNER = os.path.join(os.getcwd(), 'EduNova-master')
if INNER not in sys.path:
    sys.path.insert(0, INNER)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edunova_project.settings')
django.setup()
from django.contrib.auth.models import User
if User.objects.count() == 0:
    print('==> Base de datos vacia, cargando usuarios y roles iniciales...')
    exec(open('EduNova-master/crear_usuarios.py', encoding='utf-8-sig').read())
    exec(open('EduNova-master/crear_datos_demo.py', encoding='utf-8-sig').read())
    print('==> Datos cargados exitosamente!')
else:
    print('==> Base de datos lista con usuarios existentes.')
" || true

PORT_TO_USE="${PORT:-8000}"
echo "==> Iniciando Gunicorn en 0.0.0.0:${PORT_TO_USE}..."
exec gunicorn edunova_project.wsgi:application --bind "0.0.0.0:${PORT_TO_USE}" --workers 2 --timeout 120
