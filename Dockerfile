FROM python:3.12-slim

# Variables de entorno para Python y producción
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Copiar archivos de dependencias
COPY EduNova-master/requirements.txt /app/EduNova-master/
COPY requirements.txt /app/

# Instalar dependencias con pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . /app/

# Compilar archivos estáticos para WhiteNoise
RUN python manage.py collectstatic --no-input

# Puerto expuesto por defecto
EXPOSE 8000

# Iniciar servidor Gunicorn en el puerto asignado dinámicamente por Railway o la nube
CMD ["sh", "-c", "gunicorn edunova_project.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2"]
