# Instalación, producción, respaldos y piloto

## Estado y alcance

Se implementaron controles de producción, límites persistentes de acceso, sincronización de sesiones entre pestañas, redirecciones de rutas estudiantiles antiguas, herramientas de instalación y OCR, respaldos automáticos y manuales con restauración separada, panel de preparación y una cohorte sintética de API.

El correo real requiere la cuenta de Gmail/Workspace y su contraseña de aplicación, ingresadas por el administrador en el panel. El despliegue necesita un servidor y dominio reales. La revisión pedagógica y el piloto requieren docentes y alumnos autorizados. Ninguna de estas validaciones se marca como completada automáticamente.

## Instalación local desde cero en Windows

Requisitos: Python 3.12, Node.js 22, pnpm 11.25.0 y Ollama instalado desde su distribución oficial. Usa un solo gestor de dependencias para el frontend.

Desde la raíz del repositorio:

```powershell
npm install -g pnpm@11.25.0
.\setup.ps1 -Ocr
ollama pull llama3.2:3b
.\run-modern.ps1
```

El instalador crea `.venv`, instala dependencias, genera `.env` con una clave aleatoria propia y descarga los modelos OCR oficiales de español e inglés con revisión SHA-256. No imprime las credenciales. Si `.env` ya existe, conserva las claves privadas e integraciones; una clave conocida de demostración se reemplaza. Cambiar esa clave invalida las sesiones previas. El entorno de desarrollo conserva las cuentas demo y configura respaldos cada 24 horas, reteniendo las últimas siete copias.

Las dependencias se instalan una vez. Para reconfigurar sin reinstalarlas usa `setup.ps1 -SkipDependencies`. Abrir la terminal en la raíz evita que se use otro `.env`. El script de arranque usa los puertos 3000 y 8000 y detecta servicios ya iniciados; Ollama usa el 11434.

En Linux puedes usar `.venv/bin/python` y `requirements-linux.txt`; las herramientas Python son las mismas. Ejecuta `pnpm install --frozen-lockfile` dentro de `frontend-modern`.

## Configuración y diagnóstico sin publicar secretos

```powershell
.\.venv\Scripts\python.exe -m tools.manage configure
.\.venv\Scripts\python.exe -m tools.manage ocr
.\.venv\Scripts\python.exe -m tools.manage doctor
```

`doctor` revisa configuración y el último respaldo. La prueba de conexión de IA se ejecuta desde Superadmin → Estado de integraciones; la prueba de correo desde Configurar correo Gmail. Que una integración esté configurada no demuestra que responda ni que el mensaje llegue.

Superadmin → **Preparación y respaldos** muestra pendientes, el archivo de respaldo más reciente y documentos faltantes. Permite crear una copia manual. Ni docentes ni ayudantes pueden acceder a ese panel o su API. No hay restauración destructiva desde la web.

## Producción y HTTPS con Docker Compose

Se preparó un despliegue con proxy Caddy, frontend Next, backend, Ollama y volúmenes persistentes. Solo se publican 80 y 443. [Caddy gestiona HTTPS](https://caddyserver.com/docs/automatic-https) y [admite WebSocket en el proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy). El esquema sigue la recomendación de [Next.js de usar un proxy inverso](https://nextjs.org/docs/app/guides/self-hosting).

Antes de publicar: dominio apuntando al servidor, puertos 80/443 disponibles y Docker Engine/Compose activos. Los contenedores de la aplicación usan un usuario sin privilegios. La subred de Compose es `172.30.241.0/24`; si colisiona con tu red, cambia también la IP de Caddy y `--forwarded-allow-ips` del backend. La aplicación solo confía en esa IP para conocer la dirección del cliente, no en un `X-Forwarded-For` recibido directamente de Internet.

Genera un archivo privado nuevo con **tu dominio**, sin reutilizar el `.env` de desarrollo:

```powershell
.\.venv\Scripts\python.exe -m tools.manage --env-file deploy/runtime/.env configure --environment production --url https://integrieval.tu-dominio.cl --docker
docker compose --env-file deploy/runtime/.env -f deploy/compose.yaml config --quiet
docker compose --env-file deploy/runtime/.env -f deploy/compose.yaml up -d ollama
docker compose --env-file deploy/runtime/.env -f deploy/compose.yaml run --rm model-init
docker compose --env-file deploy/runtime/.env -f deploy/compose.yaml up -d --build
docker compose --env-file deploy/runtime/.env -f deploy/compose.yaml exec backend python -m tools.manage create-admin --email administrador@tu-dominio.cl --name Administrador
docker compose --env-file deploy/runtime/.env -f deploy/compose.yaml exec backend python -m tools.manage ocr
docker compose --env-file deploy/runtime/.env -f deploy/compose.yaml restart backend
```

El comando `create-admin` solicita la contraseña sin mostrarla ni incluirla en argumentos. No cambia una cuenta existente. En Linux, el directorio privado `deploy/runtime` debe ser escribible por UID 1000 y su `.env` solo legible por ese usuario (`chown -R 1000:1000 deploy/runtime` y `chmod 700 deploy/runtime; chmod 600 deploy/runtime/.env`). Esto permite guardar SMTP de forma atómica. No montes únicamente el archivo `.env` ni pases las variables SMTP como entorno del contenedor: se perdería la actualización persistida por el panel al reiniciar.

El despliegue usa un solo proceso de backend con SQLite. No escales réplicas de la API sin migrar la base y coordinar cola, recordatorios, respaldos y WebSockets. Ollama en este Compose funciona con CPU por defecto; la aceleración GPU depende del servidor. La descarga del modelo y su capacidad deben validarse en ese servidor. Antes del uso institucional fija y registra los digests de las imágenes de infraestructura probadas.

Producción rechaza clave de sesión conocida o corta, cuentas demo habilitadas, IA simulada, URL HTTP/local, CORS abierto y hosts sin dominio explícito. Las cuentas demo previamente existentes también quedan bloqueadas, incluyendo sus tokens y recuperación de contraseña. Desarrollo mantiene su funcionamiento habitual.

Las solicitudes de inicio de sesión se limitan por dirección del cliente y cuenta (ocho por ventana de quince minutos), además de sesenta por minuto por dirección. Recuperación admite diez solicitudes por minuto por dirección. El estado persiste en SQLite. Las claves de los contadores se almacenan como HMAC; no se guardan direcciones ni correos en claro en esa tabla.

La conexión docente en tiempo real utiliza el mismo dominio y transmite la credencial en el protocolo de la conexión, fuera de la URL. La API ya no acepta el token docente en parámetros de URL para evitar su aparición en registros de proxy. En producción también comprueba el origen del WebSocket. Después de actualizar, recarga las pestañas de la aplicación para usar este protocolo.

## Correo real y acceso desde otro dispositivo

1. Abre Superadmin → Configurar correo Gmail.
2. Guarda la cuenta y la contraseña de aplicación en el formulario privado.
3. Envía la prueba a tu propia dirección; verifica entrada y spam.
4. Confirma recepción y activa los envíos.
5. Abre un enlace de prueba desde otro dispositivo. `localhost` no sirve para los alumnos en otro equipo.
6. Prueba recuperación de contraseña y avisos de cita con cuentas autorizadas.

La URL de producción se cambia en el archivo de configuración del servidor junto con CORS y el proxy, no desde el formulario de Gmail. No se enviaron mensajes reales como parte de la implementación.

## Respaldo y restauración

```powershell
.\.venv\Scripts\python.exe -m tools.manage backup
.\.venv\Scripts\python.exe -m tools.manage verify backups/NOMBRE.backup.zip
.\.venv\Scripts\python.exe -m tools.manage restore backups/NOMBRE.backup.zip --output restored-data
```

La copia contiene una instantánea consistente de SQLite y los documentos referenciados que están dentro de las carpetas administradas. Cada archivo lleva tamaño y SHA-256. La copia se verifica antes de publicarse; un fallo conserva las copias anteriores. Los documentos que faltan en el disco se informan expresamente; una copia incompleta no aparece como lista para producción. No se incluyen `.env`, contraseñas de SMTP, modelos de Ollama ni datos OCR.

La API debe estar encendida para que se ejecuten las copias automáticas. `BACKUP_ENABLED=true`, `BACKUP_INTERVAL_HOURS=24`, `BACKUP_KEEP=7` y `BACKUP_DIR` controlan el proceso. El intervalo admite de 1 a 168 horas y la retención de 2 a 90 archivos. Un respaldo más antiguo que dos intervalos aparece vencido. La retención se aplica solo a archivos generados por esta herramienta en la carpeta configurada.

La restauración exige una carpeta nueva y conserva la base activa. Ajusta las rutas de documentos a su nueva ubicación, invalida sesiones y enlaces de recuperación, desactiva la verificación SMTP y cancela correos pendientes para evitar su reproducción automática. Los trabajos en cola se marcan para revisión y reintento. No modifica el historial de auditoría.

Al iniciar, la API deshabilita los envíos si la base no contiene la verificación de la configuración SMTP actual, incluso si el archivo de entorno tenía los envíos activados. Esto evita reanudar correos al restaurar una base sin verificación vigente; el administrador debe repetir la prueba y activación desde el panel.

Para usar una restauración: detén la API, conserva una copia de los datos actuales, configura `DATABASE_URL`, `UPLOAD_DIR`, `MATERIALS_DIR` y `WORKS_DIR` hacia `restored-data`, establece `SMTP_ENABLED=false`, inicia, revisa datos y revalida correo antes de activarlo. Los Flash Tests conservan tiempos y vigencias originales. No se detienen los cronómetros por restaurar una copia.

Las copias contienen datos de estudiantes, aunque no incluyan la configuración privada. Guárdalas con permisos restringidos y conserva otra copia protegida fuera del equipo. SHA-256 detecta alteraciones accidentales; no autentica a quien creó un archivo ni sustituye cifrado. Esta herramienta no sube respaldos a terceros.

## Pruebas de carga y piloto

```powershell
.\.venv\Scripts\python.exe -m tools.loadtest --users 30 --concurrency 10 --output pilot-results/load-30.json
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

La cohorte usa una base temporal, sesiones sintéticas y seis solicitudes por alumno: información, inicio, respuesta, recuperación de avance, segunda respuesta y resultado. No toca alumnos reales ni llama a correo u Ollama. Mide latencia de API dentro del proceso, no red, navegador, GPU ni calidad pedagógica. La medición local con 30 alumnos y concurrencia 10 terminó con 180 solicitudes y cero errores; no es una promesa de capacidad en otro servidor.

Usa [PILOTO.md](PILOTO.md) para la revisión con personas. Registra datos reales y resultados fuera de Git, en `pilot-results/` o almacenamiento institucional autorizado. Las rutas antiguas de detalle/sesión redirigen al portal del alumno; el único flujo de evaluación estudiantil es el enlace personal.

## Límites de la validación actual

- Pruebas automatizadas de API, configuración, límites, respaldo/restauración y cohorte aislada ejecutadas localmente.
- Compilación Next/TypeScript y revisión de navegación local.
- Docker Compose preparado y validado como configuración; el motor Docker no estaba encendido, por lo que no se construyeron ni ejecutaron contenedores ni se emitieron certificados reales.
- Pendientes externos: cuenta de correo, dominio/servidor, revisión pedagógica y piloto autorizado con alumnos y dispositivos reales.
