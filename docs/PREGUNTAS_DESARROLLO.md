# Preguntas de desarrollo en el pool

## Uso docente

1. En **Pool de Preguntas**, selecciona el informe del estudiante. También puedes abrir su pool desde Trabajos y Análisis IA.
2. Pulsa **Agregar Pregunta Propia** y elige **Desarrollo (respuesta escrita)**.
3. Escribe el enunciado y los criterios de evaluación. La respuesta de referencia es opcional. La pauta es privada del docente.
4. Guarda y selecciona la pregunta junto con las alternativas que quieras incluir en el Flash Test.
5. Revisa el tiempo por pregunta en los parámetros de la evaluación. El tiempo es común a todas las preguntas; no se asigna un tiempo adicional automáticamente al desarrollo.

La generación automática con IA sigue produciendo alternativas. Las preguntas de desarrollo se agregan manualmente. Las preguntas despachadas mantienen un snapshot de enunciado y pauta y no pueden editarse.

## Respuesta del estudiante

Las preguntas de desarrollo muestran un área de texto de hasta 5.000 caracteres. El texto se guarda después de una pausa breve y se vuelve a intentar al recuperar conexión; solo lo que recibe el servidor queda persistido. **Enviar respuesta y continuar** avanza a la siguiente pregunta. No se permite volver atrás.

Si vence el tiempo se conserva el último texto que llegó al servidor. Una pregunta sin respuesta recibe cero puntos. El cronómetro continúa durante desconexiones y recargas. El contenido pendiente de envío en el navegador puede perderse si se cierra la página antes de guardarse.

La API pública del alumno no devuelve respuestas correctas, criterios ni respuestas de referencia. El resultado se muestra como **Pendiente de revisión docente** mientras existan respuestas escritas sin corregir. El alumno puede actualizar la revisión desde esa pantalla o recargar el enlace para consultar el resultado guardado.

## Corrección y puntaje

Las respuestas se revisan desde el propio pool, en **Revisión de desarrollo**, o en Resultados y Citas cuando quedan correcciones pendientes. El docente o ayudante autorizado asigna de 0 a 100 puntos a cada respuesta y debe justificar su criterio. No se usa corrección automática por IA para estas respuestas.

Cada pregunta tiene el mismo peso. Por ejemplo, una alternativa correcta (100) y un desarrollo con 50 puntos producen un Flash Test de 75%. Hasta revisar todas las respuestas escritas, el puntaje Flash permanece pendiente y el cierre de calificación se bloquea. La revisión y sus cambios quedan auditados. Una calificación cerrada no permite modificar estas revisiones.

## Compatibilidad y validación

La migración SQLite agrega los campos de tipo y pauta sin eliminar preguntas existentes. Las preguntas anteriores conservan el tipo de alternativas; los snapshots anteriores siguen funcionando. Se crea una copia de seguridad antes de modificar una tabla antigua.

Se probaron creación, edición, validación, privacidad de pauta, recuperación del texto, vencimiento, corrección manual, cierre de calificación, permisos y migración idempotente. Suite de backend: 108 pruebas aprobadas. Una cohorte aislada de 30 alumnos y 180 solicitudes de Flash Test completó sin errores después de corregir el bloqueo de guardados concurrentes. Esa cohorte no equivale a una prueba real con alumnos.
