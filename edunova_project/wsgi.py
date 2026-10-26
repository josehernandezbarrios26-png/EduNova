"""
WSGI config for edunova_project (Root wrapper for Render/Production).
"""
import os
import sys
from pathlib import Path

# Add EduNova-master to sys.path so edunova_project.settings and apps are resolved
INNER_DIR = Path(__file__).resolve().parent.parent / 'EduNova-master'
if str(INNER_DIR) not in sys.path:
    sys.path.insert(0, str(INNER_DIR))

try:
    os.chdir(str(INNER_DIR))
except Exception:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edunova_project.settings')

import django
django.setup()

# Auto-migrate on startup in Render so the database is always ready
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)
except Exception as exc:
    print(f"Auto-migration note: {exc}")

# Auto-collectstatic on startup if not already run during build
try:
    from django.conf import settings
    if not (settings.STATIC_ROOT and Path(settings.STATIC_ROOT).exists()):
        from django.core.management import call_command
        call_command('collectstatic', interactive=False)
except Exception as exc:
    print(f"Auto-collectstatic note: {exc}")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
