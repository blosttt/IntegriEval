# Flash Test moderno y procesamiento de informes completos

Cambios locales del 26 de octubre de 2026:

- `/flash/{token}` es una pantalla React con el estilo compartido de IntegryEval, instrucciones, alternativas, cronómetro y resultado. `/test/{token}` redirige a ella tanto en Next como en FastAPI; ya no se sirve el HTML antiguo.
- El navegador consulta la API cada 1,5 segundos y después de cada respuesta. La API conserva el avance y controla los tiempos. Recargar o perder conexión no pausa el cronómetro. Las solicitudes tienen un tiempo máximo de 15 segundos y el cliente vuelve a sincronizar automáticamente.
- El cliente solo pide el resultado cuando el servidor ya marcó el test como completado. Una respuesta no confirmada se recupera consultando el estado; el navegador nunca calcula ni reemplaza la calificación.
- Si un proveedor real falla, devuelve una estructura inválida o no puede generar el pool completo, el procesamiento devuelve un error recuperable. No se crean notas ni preguntas simuladas como respaldo automático.
- El modo `mock` sigue disponible para demostraciones si se configura explícitamente. Los resultados históricos identificados como simulados no pueden despacharse como evaluaciones reales cuando el proveedor está en modo real. Los trabajos cuyo análisis está incompleto tampoco pueden despacharse.
- La evaluación y las preguntas se reemplazan juntas, después de obtener ambos resultados. Un fallo conserva la evaluación anterior, marca el trabajo con error y permite reintentar desde «Reanalizar con IA» o desde la cola. Los valores anteriores son históricos hasta completar el reintento.
- Los informes mayores de 8.000 caracteres se dividen en secciones consecutivas de hasta 6.000 caracteres. Se lee cada sección y se extraen evidencias y resúmenes acotados. Si el conjunto sigue siendo extenso, se sintetiza por niveles; no se descarta la cola del documento. El mismo proceso se aplica al material de apoyo y a la generación de preguntas.
- La evaluación registra caracteres originales, número de secciones y estrategia en `desglose.cobertura_documento`. La síntesis puede perder matices y requiere revisión pedagógica; el tiempo crece con el tamaño del documento. Un fallo en cualquier sección interrumpe la evaluación completa.

Validación: 73 pruebas de backend aprobadas y compilación Next/TypeScript correcta. Las pruebas incluyen cobertura del final de documentos largos, síntesis de varios niveles, fallos de IA, preservación de notas previas, reintentos, enlaces antiguos y sesiones cronometradas persistentes. La validación pedagógica y las pruebas de carga con alumnos siguen pendientes.

También se ejecutó una prueba real con Ollama sobre un informe sintético de 9.037 caracteres: dos secciones procesadas y evaluación identificada como `ollama`, sin simulación. No se utilizaron documentos personales en esa prueba.
