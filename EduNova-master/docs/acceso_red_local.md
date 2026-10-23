# Acceso de EduNova en la red local

## 1. Requisitos

- Computador servidor con EduNova abierto en VS Code.
- Python instalado.
- Dependencias del proyecto instaladas.
- Conexión a la misma Wi-Fi o LAN que los demás computadores.
- Puerto 8000 disponible en el equipo servidor.

## 2. Framework y estructura

EduNova está basado en Django. El punto de arranque del proyecto es:

- `manage.py`
- `edunova_project/settings.py`
- `edunova_project/urls.py`

La aplicación se ejecuta en el mismo servidor local y comparte la misma base de datos mientras el proceso esté activo.

## 3. Iniciar el servidor para red local

Desde la carpeta del proyecto, ejecuta:

```powershell
python manage.py runserver 0.0.0.0:8000
```

Esto hace que Django escuche en todas las interfaces del equipo local, mientras la aplicación sigue siendo accesible solo dentro de la red local y no se expone públicamente a Internet.

## 4. Obtener la IP local del servidor

En Windows, abre PowerShell y ejecuta:

```powershell
ipconfig
```

Busca la sección del adaptador que estás usando, por ejemplo:

- Wi‑Fi
- Ethernet

Y toma la línea:

```text
IPv4 Address . . . . . . . . . . . : 192.168.1.25
```

Esa es la IP que debes usar desde otros equipos de la misma red.

## 5. Acceder desde otro computador

Desde cualquier equipo conectado a la misma Wi‑Fi o LAN, abre el navegador y escribe:

```text
http://192.168.1.25:8000
```

Reemplaza la IP por la que obtuviste en tu equipo servidor.

## 6. Firewall de Windows

No es necesario desactivar el Firewall. Lo recomendado es permitir solo el puerto 8000 en redes privadas/locales.

### Crear regla de entrada en Windows

1. Abre `Windows Defender Firewall with Advanced Security`.
2. Entra a `Inbound Rules`.
3. Selecciona `New Rule`.
4. Elige `Port`.
5. Marca `TCP` y escribe `8000`.
6. Selecciona `Allow the connection`.
7. Marca `Private`.
8. Asigna un nombre como: `EduNova Local 8000`.

Esto permite que otros equipos de la red local puedan acceder al servidor sin abrir puertos adicionales ni exponer el sistema a Internet.

## 7. Seguridad aplicada

La configuración del proyecto incluye:

- `ALLOWED_HOSTS` limitado a hosts locales y de la red local.
- `CSRF_TRUSTED_ORIGINS` con orígenes locales de `http://IP:8000`.
- No se usa acceso público ni wildcard.
- Se mantienen los permisos y roles del proyecto.

## 8. Verificación rápida

Luego de iniciar la aplicación, prueba:

- `http://127.0.0.1:8000`
- `http://IP_LOCAL_DEL_SERVIDOR:8000`
- Login
- Dashboard
- Roles y permisos
- Calificaciones
- Boletines

## 9. Solución de problemas comunes

### El otro equipo no puede conectarse

Revisa este orden:

1. ¿El servidor sigue ejecutándose?
2. ¿La IP local es correcta?
3. ¿Ambos equipos están en la misma red Wi‑Fi/LAN?
4. ¿El puerto 8000 está abierto en el Firewall?
5. ¿La IP del servidor aparece en `ALLOWED_HOSTS`?
6. ¿El navegador usa `http://IP_LOCAL:8000` y no `127.0.0.1`?
7. ¿Hay VPN, antivirus o firewall adicional bloqueando la conexión?
8. ¿El router o la red corporativa impide la comunicación entre equipos?

### El navegador carga la página pero sin estilos

Verifica que el proyecto esté sirviendo archivos estáticos y que `DEBUG=True` en desarrollo.

### El navegador falla con CSRF o login

Confirma que la URL local está incluida en `CSRF_TRUSTED_ORIGINS`.

## 10. Comando final recomendado

Para usar la aplicación en red local, la forma recomendada es:

```powershell
python manage.py runserver 0.0.0.0:8000
```

Luego, desde otro equipo:

```text
http://192.168.1.25:8000
```

> Reemplaza la IP por la IP real del servidor.

## 11. Importante

Esta configuración está pensada solo para uso local dentro de la red privada. No se habilita acceso público ni exposición a Internet.
