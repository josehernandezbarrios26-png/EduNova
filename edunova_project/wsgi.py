"""
WSGI config for edunova_project.
"""
import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto Django a sys.path
INNER_DIR = Path(__file__).resolve().parent.parent / 'EduNova-master'
if str(INNER_DIR) not in sys.path:
    sys.path.insert(0, str(INNER_DIR))

try:
    os.chdir(str(INNER_DIR))
except Exception:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edunova_project.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
