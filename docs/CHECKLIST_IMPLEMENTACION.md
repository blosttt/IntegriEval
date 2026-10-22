# Checklist de implementación

Estado al 22 de octubre de 2026. Las casillas marcadas indican código implementado y verificado con el alcance descrito; no equivalen a validación de producción.

## Requisitos de interfaz y permisos

- [x] Recuperar el diseño moderno y unificar las pantallas con la marca IntegryEval y el logo UCT.
- [x] Integrar el acceso de docente, ayudante y superadministrador en la página principal.
- [x] Tutorial contextual que destaca controles y recorre el flujo dentro de la página.
- [x] Asignaturas creadas y administradas por superadmin; docentes limitados a los cursos asignados.
- [x] Directorio de profesores y ayudantes; superadmin puede abrir y administrar su espacio conservando su identidad en la auditoría.
- [x] Crear, editar, desactivar y asignar cuentas docentes a cursos.
- [x] Nómina con alta individual, importación CSV, edición y retiro conservando el historial.
- [x] Ayudante con funciones de evaluación y nómina de solo lectura, también protegido en la API.
- [x] Estudiante sin cuenta, con acceso mediante el enlace personal de su Flash Test activo.
- [x] Varias evaluaciones por asignatura, con informes, preguntas, Flash Tests, citas y resultados independientes.
- [x] Selector de evaluación y análisis desplegable.
- [x] Fecha y horario de revisión elegidos por el docente, con reprogramación.
- [x] Navegación hacia atrás conservando sesión y contexto; un error temporal de conexión no elimina la sesión.
- [x] Datos demo aditivos y reutilizables sin borrar registros existentes.

## Lista de pendientes solicitada y resultado

1. **IA real**
   - [x] Instalar Ollama local y descargar `llama3.2:3b` en este equipo.
   - [x] Probar conexión, análisis de informe sintético y generación real de 10 preguntas validadas.
   - [x] Activar el proveedor local en `.env` y distinguir respuestas reales de respaldos simulados.
   - [ ] Validar la calidad pedagógica de los resultados con docentes y casos representativos.
2. **Envío real de correos**
   - [x] Implementar integración SMTP y enlaces configurables mediante `PUBLIC_APP_URL`.
   - [ ] Configurar la cuenta SMTP y una URL accesible por los destinatarios.
   - [ ] Verificar entrega real, recepción y acceso al enlace desde otro dispositivo. SMTP sigue desactivado.
3. **Recuperación de contraseña**
   - [x] Formulario, enlace de un solo uso con caducidad, invalidación de enlaces anteriores y revocación de sesiones.
   - [ ] Verificar el flujo por correo real después de configurar SMTP.
4. **Historial de envíos y reintentos**
   - [x] Registro persistente de estados, errores e intentos y reintento desde la interfaz.
   - [x] Impedir reenvíos de Flash Tests vencidos y avisos de citas reemplazados por una actualización.
5. **Archivar o cerrar evaluaciones**
   - [x] Cierre, archivo y reapertura conservando el historial.
   - [x] Bloquear modificaciones y evitar el cierre con Flash Tests activos o archivos en cola.
6. **Exportar resultados**
   - [x] CSV UTF-8 compatible con Excel y resumen PDF por evaluación.
   - [x] Neutralizar fórmulas en los campos de texto del CSV.
   - No se genera un archivo XLSX nativo; el formato compatible con Excel es CSV.
7. **Notificaciones y recordatorios de citas**
   - [x] Avisos de creación y cambios, y recordatorio en las 24 horas anteriores.
   - [x] Registro persistente para evitar repetir el mismo recordatorio por fecha programada.
   - [ ] Verificar entrega real después de configurar SMTP.
8. **Agenda sin conflictos**
   - [x] Validar fechas futuras, bloque horario, disponibilidad y choques de docente o alumno.
   - [x] Almacenar fechas en UTC y mostrarlas en la zona configurada de Chile.
   - [x] Probar dos reservas simultáneas del mismo horario: solo una se acepta.
9. **OCR para PDF escaneados**
   - [x] Instalar modelos oficiales de español e inglés y habilitar OCR en este equipo.
   - [x] Extraer texto real de un PDF compuesto únicamente por una imagen.
   - [x] Informar errores de extracción y omitir páginas en blanco.
   - En otro equipo es necesario instalar los datos de idioma y configurar su ubicación.
10. **Carga masiva con seguimiento**
    - [x] Cola persistente por archivo, estados, progreso del lote y número de intentos.
    - [x] Cancelar pendientes y reintentar errores individualmente.
    - [x] Volver a comprobar permisos al procesar y detectar trabajos interrumpidos.
    - Los archivos que ya están procesándose terminan su ejecución; no se interrumpen a mitad de una transacción.
11. **Concurrencia, sesiones y dispositivos móviles**
    - [x] Suite de 60 pruebas automatizadas aprobadas, incluyendo permisos, reservas concurrentes y sesiones caducadas.
    - [x] Revisión visual móvil y corrección del desbordamiento de los selectores.
    - [ ] Prueba de carga con una cohorte representativa y medición de capacidad y tiempos.
    - [ ] Ensayo prolongado de sesiones y flujo completo en distintos dispositivos reales.
12. **Validación completa antes del uso con alumnos**
    - [x] Pruebas locales de la aplicación y pruebas reales separadas de Ollama y OCR.
    - [ ] Piloto integral con docente y alumnos autorizados, correo real e IA real.

## Publicación y reproducibilidad

- [x] Código, scripts de arranque y configuración de ejemplo preparados para GitHub.
- [x] Excluir `.env`, credenciales locales, bases de datos, archivos subidos, binarios, modelos, dependencias y cachés.
- [x] Documentar la instalación y el estado de las integraciones en [AVANCE_FUNCIONALIDADES.md](AVANCE_FUNCIONALIDADES.md).

Los pesos de Ollama y los datos de Tesseract están instalados localmente; no se distribuyen en Git. La cola y los recordatorios requieren que la API esté encendida.
