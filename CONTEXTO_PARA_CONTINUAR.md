# Contexto para continuar IntegryEval en otro PC

Actualizado el 22 de noviembre de 2026. Síntesis de decisiones y estado técnico del chat, no exportación literal de la conversación.

## Cómo retomar

Clona https://github.com/blosttt/IntegriEval, abre una conversación con el asistente desde la carpeta clonada y pega:

> Lee CONTEXTO_PARA_CONTINUAR.md y comprueba el código actual. Quiero preparar ESTE equipo como servidor de IntegryEval con Ollama local y una URL pública HTTPS, evitando una mensualidad de hosting. El PC anterior NO será servidor. Comprueba sistema operativo, recursos y conectividad. Continúa con instalación, inicio automático, respaldos y publicación por túnel. Conserva el historial y no publiques secretos. Prepara producción antes de mantener acceso público. Registra lo que pruebes realmente.

El archivo permite reconstruir el contexto de trabajo, pero no importa automáticamente los mensajes originales.

## Proyecto

Repositorio oficial: https://github.com/blosttt/IntegriEval
Rama publicada: main.
Referencia antes de este documento: 6699a13, con el último MVP.

Proyecto de tesis para evaluación de informes y proyectos con apoyo de IA y revisión docente. El profesor define rúbrica y temas, carga materiales e informe, revisa preguntas y envía el Flash Test. El estudiante responde y el docente revisa evidencia y desempeño.

Público interdisciplinario. Explicar con ejemplos y lenguaje claro.
La comparación docente/IA se usa exclusivamente para calibrar la IA. La calificación final queda a cargo del docente.
La agenda y gestión del curso son herramientas opcionales.

## Objetivo inmediato y decisiones de hosting

- El usuario usará OTRO PC dedicado como servidor.
- El PC de la conversación anterior no se publicará.
- Desea evitar una mensualidad de hosting y mantener funcionando la IA.
- Todo puede correr en el PC nuevo. Render ejecuta servicios en infraestructura de Render, no en el PC doméstico.
- La opción propuesta para URL gratuita es Tailscale Funnel. No está instalado ni configurado como parte de este traspaso.
- El sistema operativo, hardware, red y cuenta del equipo nuevo todavía son desconocidos.
- El coste eléctrico y la conexión dependen del equipo. Disponibilidad exige que el PC permanezca encendido y conectado.

## Arquitectura y ejecución

| Parte | Implementación |
|---|---|
| Página | frontend-modern, Next.js 16 y React 19, puerto 3000 |
| API | backend/app, Python 3.12, FastAPI, Uvicorn, puerto 8000 |
| Datos | SQLAlchemy y SQLite, integrieval.db |
| IA | Ollama y llama3.2:3b, puerto 11434 |
| PDF | PyMuPDF con OCR español/inglés opcional |
| Correo | Gmail/Workspace SMTP, panel Superadmin |
| Frontend | pnpm y pnpm-lock.yaml |
| Operación | Cola de archivos, reloj, avisos y respaldos dentro de la API |

El frontend dirige /api y /ws hacia la API.
El túnel debe publicar únicamente el puerto 3000. API y Ollama quedan locales.
Mantener una instancia de API y un worker de Uvicorn con SQLite. Múltiples procesos requieren revisar cola, cronómetros, recordatorios y WebSockets.

## Funciones disponibles

- Roles docente, ayudante y superadmin, con permisos por curso.
- Asignaturas administradas por superadmin. Docentes ven cursos asignados.
- Ayudante realiza tareas docentes con nómina de solo lectura.
- Alumnos acceden mediante enlaces individuales.
- Nómina CSV e individual, materiales y varias evaluaciones por asignatura.
- Rúbrica con criterios y pesos que suman 100, temas y plantillas reutilizables en el curso.
- Contexto diferenciado entre rúbrica, material de clase de una evaluación y material del semestre.
- Cada informe conserva la versión de la rúbrica aplicada.
- Ollama real para análisis y generación. Los fallos reales permiten reintento y no generan automáticamente resultados simulados.
- Con rúbrica se preparan al menos 3N candidatas para un test de N preguntas.
- Pool general docente, pool por informe, sorteo, cobertura de criterios e historial de asignación.
- Preguntas de alternativas, verdadero/falso y desarrollo.
- Desarrollo con pauta privada, borrador guardado y corrección manual de 0 a 100.
- Calificación pendiente mientras falten correcciones de desarrollo.
- Repreguntas de ayuda preparadas y revisadas antes del envío.
- Reporte cualitativo con citas verificables, fortalezas, debilidades y sugerencias para entrevista.
- Registro de preguntas y respuestas exactas.
- Revisión independiente del docente antes de revelar la de IA.
- Reevaluación con comentarios docentes y comparación del error.
- Tarjetas de desempeño y PDF individual.
- Citas, disponibilidad, notificaciones, auditoría y exportación CSV/PDF.
- Copias de seguridad y restauración en carpeta separada.

### Regla pedagógica definitiva de repreguntas

El usuario y su compañero corrigieron expresamente el diseño inicial:

1. Acierto: seguir con la siguiente pregunta prevista.
2. Error, omisión o tiempo agotado sin respuesta: ofrecer la MISMA ayuda sobre el concepto.
3. Conservar intento inicial y respuesta tras ayuda en el reporte.
4. No revelar la respuesta mediante la ayuda.
5. La pregunta base es de alternativas. No se implementó clasificación dinámica de respuestas de desarrollo.
6. La ayuda reemplaza el siguiente espacio, conservando cantidad y tiempo por pregunta, con las restricciones de criterio y tipo que valida la API.

No restaurar la antigua variante que daba una pregunta más difícil tras acertar.

### Último MVP publicado

- Docente configura apertura y cierre por evaluación.
- Antes de apertura se puede consultar el enlace, pero no iniciar.
- Al cierre, el intento en curso se entrega con las respuestas guardadas.
- Fechas almacenadas en UTC. El formulario muestra zona del dispositivo.
- Retroalimentación publicada por intento, visible para el alumno en su resultado.
- Docente habilita UN segundo intento, con primero completado y nota abierta.
- Cada intento conserva enlace, respuestas y puntaje propios.
- El primer resultado ofrece acceso al segundo.
- El panel operativo usa el último intento. El historial conserva los anteriores.
- Habilitar segundo intento no envía por sí solo un correo nuevo.

## Evidencia conocida

En el PC anterior pasaron 115 pruebas de backend y la compilación frontend/TypeScript. La suite incluye apertura, cierre, comentario y repetición.
Se verificaron PDF, Ollama real y recalibración con datos ficticios.
Recalibrar el mismo caso no prueba mejora en casos nuevos.
Estas verificaciones no certifican el PC nuevo. Repetir instalación, salud, IA real, OCR, correo, reinicio y acceso externo.

## Pendientes

### Servidor nuevo

- Revisar Windows/Linux, RAM, CPU/GPU, disco y conexión.
- Instalar dependencias y descargar modelo.
- Acordar base nueva o traslado de historial privado.
- Preparar arranque automático y recuperación tras reinicios.
- Configurar URL HTTPS estable y entorno de producción.
- Crear admin propio, activar correo y probar desde otra red.
- Guardar respaldos fuera del equipo y ensayar restauración.
- Comprobar recuperación tras corte eléctrico y reconexión.

### Producto y validación

- Piloto con docentes y alumnos en varias disciplinas.
- Medir acuerdo docente/IA usando casos nuevos reservados.
- Probar entrega real de correos y flujo móvil externo.
- Medir capacidad con IA real y varios alumnos.
- Mejorar despacho por curso en la interfaz; la API admite varios alumnos.
- Pulir edición de preguntas individuales, que aún usa diálogos y alternativas JSON.
- Revisar escalabilidad antes de uso institucional.

Fuera del alcance solicitado: reconocimiento oral, proyección de tokens y comparación de plataformas. El dictado fue retirado. El profesor aún no entregó los nombres de plataformas.

## Instalación inicial Windows

Instalar Git, Python 3.12, Node.js 22 y Ollama desde fuentes oficiales. En PowerShell:

    git clone https://github.com/blosttt/IntegriEval.git
    cd IntegriEval
    npm install -g pnpm@11.25.0
    powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -Ocr
    ollama pull llama3.2:3b
    powershell -NoProfile -ExecutionPolicy Bypass -File .\start-ollama.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File .\run-modern.ps1 -Rebuild

Comprobar desde otra terminal:

    Invoke-RestMethod http://127.0.0.1:8000/api/health
    Invoke-RestMethod http://127.0.0.1:11434/api/tags

Abrir http://127.0.0.1:3000.

setup.ps1 genera un .env privado. .env.example está excluido del repositorio por decisión del usuario.
run-modern.ps1 es arranque manual. Todavía falta registrar servicios/tareas para este nuevo servidor.
Iniciar start-ollama.ps1 explícitamente: la detección del proveedor en run-modern.ps1 puede no coincidir si el .env usa comillas.

Para Linux usar Python 3.12, Node.js 22, pnpm, Ollama y requirements-linux.txt. Los .ps1 son Windows. Existe alternativa Docker Compose en deploy/compose.yaml. Leer docs/OPERACION_Y_DESPLIEGUE.md antes de elegir.

## URL pública propuesta

Tailscale Funnel puede ofrecer https://nombre-pc.nombre-red.ts.net. Los visitantes acceden desde un navegador sin instalar Tailscale.

Referencias verificadas el 22/11/2026:
- https://tailscale.com/docs/features/tailscale-funnel
- https://tailscale.com/docs/reference/tailscale-cli/funnel
- https://tailscale.com/pricing

Confirmar condiciones actuales y elegibilidad. El plan Personal gratuito es para uso no comercial. Funnel tiene límites de ancho de banda. Revisar el uso institucional antes de adoptarlo.

Secuencia pendiente:

1. Instalar Tailscale en el PC nuevo. El usuario inicia sesión y completa permisos.
2. Confirmar MagicDNS, HTTPS y autorización Funnel según documentación.
3. Preparar admin propio y producción antes de mantener acceso público.
4. Con IntegryEval activo, habilitar:

    tailscale funnel --bg 3000
    tailscale funnel status

5. Usar la URL EXACTA devuelta, no inventar un dominio.
6. Aplicarla a la configuración y reiniciar la aplicación.
7. Probar con datos móviles.
8. Preparar inicio automático de Tailscale, frontend, API y Ollama.

--bg mantiene el túnel configurado pero no inicia los otros procesos.
Mantener nombres de máquina/red para conservar la dirección.
Publicar Funnel permite acceso desde Internet a la app. El usuario debe autorizar la exposición concreta. Ollama no se expone.
Cloudflare Quick Tunnel fue considerado para demos temporales, pero su hostname cambia al crear otro túnel.

## Producción y correo

Con URL real disponible y entorno instalado:

    .\.venv\Scripts\python.exe -m tools.manage configure --environment production --url https://URL-REAL-DEL-SERVIDOR
    .\.venv\Scripts\python.exe -m tools.manage create-admin --email TU-CORREO --name Administrador

create-admin pide contraseña de forma privada.
Revisar PUBLIC_APP_URL, CORS_ORIGINS y ALLOWED_HOSTS con hostname exacto y conservar los hosts locales necesarios.
Producción deshabilita cuentas demo, exige clave privada válida, URL HTTPS y proveedor real.
Configurar Gmail/Workspace desde Superadmin, enviar prueba a cuenta autorizada y confirmar recepción antes de activar.
No guardar claves en chat ni GitHub. Ver docs/CONFIGURAR_GMAIL.md.

## Traslado de datos

GitHub contiene código. Clonar NO recupera la base local, usuarios demo creados manualmente, PDF subidos, .env, contraseñas, modelos, OCR ni respaldos del PC anterior.
Acordar qué datos se necesitan. Usar respaldo consistente y restaurar en carpeta nueva. No copiar una SQLite activa sin procedimiento.

    .\.venv\Scripts\python.exe -m tools.manage backup
    .\.venv\Scripts\python.exe -m tools.manage verify backups/NOMBRE.backup.zip
    .\.venv\Scripts\python.exe -m tools.manage restore backups/NOMBRE.backup.zip --output restored-data

Leer la guía de operación para apuntar luego a los datos restaurados y revisar rutas. Restaurar invalida sesiones y requiere revisar SMTP.
Generar configuración propia del nuevo equipo.
Para datos ficticios nuevos en desarrollo, load_demo_data.py es aditivo. Evitar seed_demo_data.py sobre historial a conservar: contiene limpieza de registros.

## Archivos clave

- backend/app/main.py — arranque, migraciones y tareas periódicas.
- backend/app/config.py — entorno, rutas y validación de producción.
- backend/app/routers/flash_test.py — despacho, reloj y respuestas.
- backend/app/routers/flash_mvp.py — fechas, retroalimentación e intentos.
- backend/app/services/adaptive.py — ayuda ante error/blanco.
- backend/app/routers/general_pool.py — banco general y sorteo.
- backend/app/routers/assessment.py — rúbrica, plantillas, PDF y calibración.
- backend/app/services/assessment.py — evidencias y puntajes por criterio.
- frontend-modern/src/components/teacher/FlashMvp.tsx — interfaz del MVP.
- tools/manage.py — configuración, admin, OCR y respaldos.
- docs/OPERACION_Y_DESPLIEGUE.md — operación y Docker.
- docs/FLUJO_RUBRICA_Y_CALIBRACION.md — flujo pedagógico.
- docs/PILOTO.md — validación con personas.

El PC anterior usaba IntegriEval-main como copia ejecutable sin .git y publish-github como clon de publicación. En el nuevo PC usar una sola copia clonada normal.
Los PPTX están fuera del repositorio y no se trasladan con este commit. Su contenido acordado usa números 1–4 y comparación docente/IA solo para calibración.

## Criterio de finalización del servidor

- [ ] Reiniciar el PC y verificar inicio automático de todos los procesos.
- [ ] Abrir URL HTTPS desde otra red.
- [ ] Ingresar con usuario propio y comprobar bloqueo de cuentas demo.
- [ ] Analizar informe con Ollama real y rúbrica.
- [ ] Rendir test, comprobar fechas y ayuda por error/blanco.
- [ ] Publicar comentario, habilitar segundo intento y descargar PDF.
- [ ] Recibir correo con URL estable.
- [ ] Reiniciar sin perder datos ni documentos.
- [ ] Verificar respaldo externo y restauración.
- [ ] Registrar límites de capacidad y validación pendientes.

No marcar pasos por inferencia. Comprobarlos en el nuevo equipo.
