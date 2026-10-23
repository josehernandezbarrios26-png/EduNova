@echo off
setlocal
cd /d "%~dp0"

if not exist "manage.py" (
    echo No se encontro manage.py en "%CD%".
    echo Asegurate de ejecutar este archivo desde la carpeta del proyecto.
    exit /b 1
)

set "LAN_IP="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-NetIPConfiguration ^| Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' } ^| ForEach-Object { $_.IPv4Address.IPAddress } ^| Select-Object -First 1" 2^>nul`) do set "LAN_IP=%%I"

if defined LAN_IP (
    set "ALLOWED_HOSTS=127.0.0.1,localhost,%LAN_IP%"
    echo EduNova estara disponible en:
    echo   Local: http://127.0.0.1:8000
    echo   Red:   http://%LAN_IP%:8000
) else (
    set "ALLOWED_HOSTS=127.0.0.1,localhost"
    echo No se pudo detectar una IPv4 de red local.
    echo El servidor iniciara localmente; verifica que este conectado a Wi-Fi o LAN.
)
echo.
echo Si otros equipos no logran conectar, permite Python en la red privada de Windows Firewall (puerto 8000).
echo No cierres esta ventana mientras uses EduNova.
echo.

if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
    python manage.py runserver 0.0.0.0:8000
    exit /b %ERRORLEVEL%
)

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
    python manage.py runserver 0.0.0.0:8000
    exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if not errorlevel 1 (
    py manage.py runserver 0.0.0.0:8000
    exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if not errorlevel 1 (
    python manage.py runserver 0.0.0.0:8000
    exit /b %ERRORLEVEL%
)

echo No se encontro Python ni un entorno virtual activo.
echo Puedes crear uno con: py -m venv venv
exit /b 1
