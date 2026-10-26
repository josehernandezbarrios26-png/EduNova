#!/usr/bin/env bash
# Build script en la raíz para Render
set -o errexit

if [ -d "EduNova-master" ]; then
  cd EduNova-master
fi

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
