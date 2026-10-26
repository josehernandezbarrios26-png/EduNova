#!/usr/bin/env python
"""Django's command-line utility for administrative tasks (Root wrapper)."""
import os
import sys
from pathlib import Path


def main():
    inner_dir = Path(__file__).resolve().parent / 'EduNova-master'
    if str(inner_dir) not in sys.path:
        sys.path.insert(0, str(inner_dir))
    try:
        os.chdir(str(inner_dir))
    except Exception:
        pass
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edunova_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
