# Registro del piloto de IntegryEval

Este documento es un protocolo sin resultados personales. Copia una versión a `pilot-results/` para registrar evidencia del piloto; esa carpeta está excluida de Git. No marques como aprobado un paso que solo se haya simulado.

## Preparación

Registra responsable, fecha, versión Git, servidor, modelo Ollama, dispositivos, número de participantes autorizados y alcance de la prueba. Usa identificadores de prueba en lugar de nombres en las mediciones técnicas. Acuerda quién revisa las preguntas y qué criterios pedagógicos se aplicarán.

## Casos y evidencia

| Caso | Resultado esperado | Evidencia requerida | Estado inicial |
|---|---|---|---|
| Cuenta docente/ayudante/admin | Accesos y acciones acordes al rol | Capturas y pruebas API | Pendiente |
| Ayudante y nómina | Puede consultar, no editar alumnos | Intento de edición rechazado | Pendiente |
| Acceso cruzado de cursos | No permite consultar ni cambiar otro curso | Respuesta de acceso denegado | Pendiente |
| Informe corto y largo | Considera métodos, resultados y conclusión final | Revisión docente del texto y análisis | Pendiente |
| IA sin conexión | No produce nota ni pool simulados; permite reintento | Estado de error y posterior recuperación | Pendiente |
| Calidad de preguntas | Contextuales, claras y con una alternativa correcta | Revisión y ajustes del docente | Pendiente |
| Correo y enlace | Llega y abre desde otro dispositivo | Recepción confirmada sin publicar el token | Pendiente |
| Flash Test y recarga | Conserva respuestas y tiempos | Reanudar tras una respuesta | Pendiente |
| Desconexión y vencimiento | El servidor mantiene tiempo y cierre | Resultado persistido | Pendiente |
| Varias pestañas y cambio de cuenta | No conserva pantalla de otro usuario | Secuencia de cierre/cambio y acceso directo | Pendiente |
| Citas y recordatorios | Fecha válida, sin solapamientos y correo recibido | Horario y recepción | Pendiente |
| Cierre y exportación | Historial conservado, datos coherentes | Comparación de pantalla y exportación | Pendiente |
| Restauración | Copia verificable y datos recuperables | Ensayo en carpeta separada | Pendiente |
| Carga representativa | Tiempos aceptados por el equipo | p50/p95, errores y tiempo real de IA | Pendiente |

## Revisión pedagógica

Para cada informe, registra si la rúbrica se aplicó correctamente, si el análisis cita evidencia del trabajo, si una síntesis perdió información relevante y si las preguntas requieren comprender el informe. Registra correcciones y decisión del docente; un porcentaje del modelo no debe tomarse como prueba de autoría por sí solo.

## Cierre

Registra incidencias, severidad, corrección y repetición del caso, junto con la decisión del responsable sobre si el sistema está listo para el alcance previsto. La aprobación del piloto y de la calidad pedagógica corresponde a las personas responsables, no se infiere del resultado de las pruebas técnicas.
