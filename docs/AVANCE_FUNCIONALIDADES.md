# Avance de funcionalidades · 21 de octubre de 2026

## Implementado en esta entrega

- Recuperación de contraseña en `/recuperar`: respuesta neutra para evitar revelar cuentas, enlace de 30 minutos de un solo uso, límite de solicitud por cuenta, hash del token, invalidación de enlaces anteriores y revocación de sesiones al cambiar la contraseña. El envío depende de SMTP.
- Historial persistente de correos de Flash Tests y citas con estados, errores e intentos. El docente puede reintentar desde la interfaz; no se reenvían invitaciones vencidas ni avisos reemplazados por una reprogramación.
- Notificación al crear, reprogramar o cambiar el estado de una cita. Recordatorio automático en las 24 horas anteriores, una vez por fecha programada. Con SMTP desactivado no se envían mensajes.
- Validación de citas futuras, coincidencia del bloque con la hora local, disponibilidad semanal y solapamientos de docente o alumno. Las fechas se guardan en UTC y se interpretan en `APP_TIMEZONE`. Una prueba usa dos conexiones simultáneas a SQLite para verificar la reserva de un mismo horario.
- Cierre y archivo reversible de evaluaciones. Se conserva el historial; los cambios requieren reabrir. No se cierra con Flash Tests activos ni cargas pendientes. También se protege la ruta de parámetros de la interfaz anterior.
- Exportación de resultados por evaluación a CSV UTF-8 compatible con Excel y a PDF. El CSV neutraliza fórmulas en campos de texto. CSV incluye notas, indicadores, revisión y cita; PDF ofrece un resumen de resultados. No se genera un archivo XLSX nativo.
- Cola persistente por archivo, con estado, número de intentos, cancelación de pendientes y reintento individual. Los archivos iniciados no se pueden cancelar: terminan su procesamiento para no interrumpir una transacción. El trabajador vuelve a comprobar permisos y estado del alumno. Se aceptan hasta 50 PDF de 20 MB cada uno.
- Ruta OCR con PyMuPDF/Tesseract. Se instalaron localmente los modelos oficiales de español e inglés y se verificó la extracción de un PDF compuesto solo por una imagen. Si el documento no tiene texto y OCR no está disponible en otro equipo, se muestra un error explícito en lugar de generar un análisis vacío.
- Panel de diagnóstico de integraciones para superadmin, con una prueba de conexión a la IA que no envía datos de alumnos ni muestra secretos.
- Ollama instalado de forma portable en `uploads/ollama/runtime`, con `llama3.2:3b` guardado localmente. Servicio limitado a `127.0.0.1:11434`. La prueba real de conexión, análisis de informe sintético y generación de 10 preguntas validadas terminó correctamente en 61 segundos, sin respaldo simulado. El proveedor se activó en `.env` con un tiempo máximo de 180 segundos por petición. Las evaluaciones nuevas registran el motor utilizado y si hubo respaldo simulado.
- Pruebas de recuperación, permisos, cola, horarios concurrentes, sesiones caducadas, exportación y archivo; revisión visual a tamaño móvil.

## Configuración y validación externa pendientes

1. Validar pedagógicamente los resultados con una pauta docente. El entorno local ya usa Ollama real, con el modelo y la prueba indicados arriba. En otro equipo hace falta instalar Ollama, descargar el modelo y configurar `.env`; no se incluyen los binarios ni los modelos en Git.
2. Configurar SMTP y una `PUBLIC_APP_URL` accesible por los destinatarios. Hacer una prueba de entrega con un correo autorizado antes de utilizarlo con alumnos. Actualmente SMTP está desactivado.
3. En otro equipo, instalar los archivos Tesseract `.traineddata` de los idiomas deseados, establecer `TESSDATA_PREFIX` y `OCR_LANGUAGE`, y activar `OCR_ENABLED`. En este entorno OCR está habilitado y fue validado. Los modelos proceden de [tesseract-ocr/tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast); la revisión y sus SHA-256 están en `uploads/ocr/source.json`, fuera del repositorio junto con los datos locales.
4. Ejecutar un piloto completo con docente y alumnos autorizados, IA y correo reales. La suite local y las pruebas de concurrencia no reemplazan una medición de carga de una cohorte ni un ensayo prolongado de sesiones con varios dispositivos.

## Operación

Instalar dependencias con `pip install -r requirements.txt`; se añadió `tzdata` para soportar las zonas horarias en Windows. Las tablas operativas se crean al iniciar la API, sin borrar los datos existentes. La cola y los recordatorios funcionan mientras la API esté encendida. Si un archivo quedó marcado en procesamiento durante más de 30 minutos tras una interrupción, se marca como error para revisión y reintento manual.

Recompilar la interfaz con `./run-modern.ps1 -Rebuild`. API local: `http://127.0.0.1:8000`; interfaz moderna: `http://127.0.0.1:3000`.

`./start-ollama.ps1` inicia el runtime local en segundo plano; `run-modern.ps1` lo invoca si `.env` selecciona Ollama. Los modelos son los de la [biblioteca oficial de Ollama](https://ollama.com/library/llama3.2). Los archivos de instalación, pesos y registros quedan en `uploads/ollama`, excluidos del repositorio. Las pruebas automatizadas aíslan SMTP y usan el motor simulado por defecto para no invocar el modelo del usuario ni enviar mensajes; la prueba real se ejecutó aparte y su resumen local queda en `uploads/ollama/probe.json`.
