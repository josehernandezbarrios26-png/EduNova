"""
Django settings for edunova_project project.
Proyecto Formativo: SISTEMAS DE INFORMACIÓN Y DESARROLLO DE SOFTWARE EN EL MAGDALENA
Software: EduNova (Sistema de Integración Técnica Education)
Centro de Logística y Promoción Ecoturística del Magdalena - ADSI 228106
"""

import socket
from pathlib import Path
from decouple import Csv, config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def _local_hosts():
    """Genera una lista segura de hosts locales, Render, Railway y de red privada."""
    hosts = ['localhost', '127.0.0.1', '[::1]', '.onrender.com', '.railway.app', '.up.railway.app']

    render_hostname = config('RENDER_EXTERNAL_HOSTNAME', default=None)
    if render_hostname:
        hosts.append(render_hostname)

    railway_domain = config('RAILWAY_PUBLIC_DOMAIN', default=None)
    if railway_domain:
        hosts.append(railway_domain)

    env_hosts = config('ALLOWED_HOSTS', default='', cast=Csv())
    hosts.extend(env_hosts)

    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip and ip not in hosts:
                hosts.append(ip)
    except Exception:
        pass

    try:
        for family, _, _, _, sockaddr in socket.getaddrinfo(hostname or 'localhost', None, type=socket.SOCK_STREAM):
            ip = sockaddr[0]
            if ip and ip not in hosts and not ip.startswith('fe80:'):
                hosts.append(ip)
    except Exception:
        pass

    return [host for host in dict.fromkeys(hosts) if host]


def _csrf_trusted_origins():
    """Registra orígenes locales, Render y Railway para peticiones seguras."""
    origins = list(config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv()))
    origins.append('https://*.onrender.com')
    origins.append('https://*.railway.app')
    origins.append('https://*.up.railway.app')

    render_hostname = config('RENDER_EXTERNAL_HOSTNAME', default=None)
    if render_hostname:
        origins.append(f'https://{render_hostname}')

    railway_domain = config('RAILWAY_PUBLIC_DOMAIN', default=None)
    if railway_domain:
        origins.append(f'https://{railway_domain}')

    for host in _local_hosts():
        if host in {'localhost', '127.0.0.1', '[::1]'}:
            origins.append(f'http://{host}:8000')
            origins.append(f'https://{host}:8000')
        elif not host.startswith('.'):
            origins.append(f'http://{host}:8000')
            origins.append(f'https://{host}')

    deduped = []
    seen = set()
    for origin in origins:
        if origin and origin not in seen:
            seen.add(origin)
            deduped.append(origin)
    return deduped


# SEGURIDAD: Llave secreta cargada desde archivo .env
SECRET_KEY = config('SECRET_KEY', default='django-insecure-edunova-default-key-adsi-2026')

# Modo de depuración (True en desarrollo formativo)
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = _local_hosts()
CSRF_TRUSTED_ORIGINS = _csrf_trusted_origins()

# Definición de aplicaciones
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Aplicaciones del Dominio EduNova
    'usuarios.apps.UsuariosConfig',
    'instituciones.apps.InstitucionesConfig',
    'academico.apps.AcademicoConfig',
    'seguimiento.apps.SeguimientoConfig',
    'evaluaciones.apps.EvaluacionesConfig',

    # API REST
    'rest_framework',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'edunova_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'edunova_project.wsgi.application'

# Configuración de Base de Datos
# Por defecto se conecta a MySQL Server si está disponible en .env; de lo contrario usa sqlite3 para pruebas locales
USE_MYSQL = config('USE_MYSQL', default=False, cast=bool)

if USE_MYSQL:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME', default='edunova_db'),
            'USER': config('DB_USER', default='root'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Validadores de contraseñas seguras (RNF-001)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internacionalización y Localización (Colombia / Español)
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Archivos Estáticos (CSS, JavaScript, Imágenes de diseño)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Archivos Multimedia (Actas escaneadas, fotos de evidencia)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Tipo de llave primaria por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Configuración de Correo Electrónico ──────────────────────────────────────
# En desarrollo usa la consola; en producción cambia a smtp con las vars del .env
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='EduNova <noreply@edunova.edu.co>')

# ── Configuración de la API REST (Django REST Framework) ─────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

