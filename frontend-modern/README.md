# Interfaz moderna recuperada

Interfaz React/Next.js recuperada de los mapas de compilación de la copia de D:, conectada al backend corregido mediante `src/lib/api.ts`.

Desde la raíz del proyecto, ejecutar `./run-modern.ps1`. Para recompilar tras editar la interfaz: `./run-modern.ps1 -Rebuild`.

- Interfaz moderna: http://127.0.0.1:3000.
- API y pantalla de Flash Test corregida: http://127.0.0.1:8000.
- Docente demo: `docente@universidad.cl` / `Docente123!`.
- Administrador: `admin@universidad.cl` / `Admin123!`.
- Estudiantes: ingresan mediante el enlace único del test, sin crear cuentas.

La interfaz conserva el diseño recuperado, con login JSON, roles, porcentajes, validaciones, selección de preguntas, despacho SMTP y recuperación del Flash Test adaptados al backend existente. Los horarios de disponibilidad se guardan por docente; las citas se agendan explícitamente desde resultados.

Una asignatura admite varias evaluaciones independientes, cada una con parámetros, informes, preguntas, Flash Tests, citas y resultados propios. El selector «Evaluación» permite cambiar de contexto y el análisis se despliega bajo demanda. Los materiales de apoyo se comparten en la asignatura y admiten PDF, Markdown y TXT. La migración de SQLite conserva los registros previos y crea una copia de seguridad local antes de actualizar el esquema.

El acceso de demostración usa las credenciales locales del backend; no se presenta como Google SSO. Con SMTP desactivado, la interfaz muestra el enlace del test y confirma que no se envió correo. Los proveedores LLM requieren configuración propia en `.env`.

Las versiones de paquetes están fijadas en `package.json` y `pnpm-lock.yaml`. Para instalar en otro equipo: Node.js compatible con Next.js 16 y `pnpm install` en esta carpeta. El script de arranque también puede usar el Node.js incluido en el entorno local de Codex.

## Permisos y flujo de uso

- El inicio usa la marca IntegryEval y el emblema oficial de la UCT; el archivo institucional y su procedencia están en `public/uct-logo.png` y `public/LOGO-SOURCE.md`.
- Solo el administrador crea y edita los datos de asignaturas, crea/edita/desactiva profesores y asigna o retira docentes de cursos. La gestión está en `/admin/dashboard`; la auditoría, en `/admin/audit`.
- Un curso admite varios docentes. Cada profesor puede ver y trabajar únicamente en los cursos asignados. Puede gestionar nómina, materiales, parámetros, informes, preguntas y resultados, pero no crear cursos ni administrar cuentas.
- Al desactivar un profesor se bloquean también sus tokens vigentes. Al retirarlo de un curso se revoca el acceso a ese curso. Las operaciones de administración y retiro conservan el historial y quedan auditadas.
- El administrador puede retirar estudiantes de un curso. Esto los quita de la nómina activa e inhabilita sus enlaces pendientes, conservando sus registros históricos.
- Las cuentas son creadas por administración; no hay autorregistro público. Los estudiantes no tienen cuenta ni acceden a cursos: entran por el enlace/token de su Flash Test activo.
- El tutorial modal se muestra la primera vez que entra cada docente. «Guía de uso» permite repetirlo. Recorrerlo selecciona los apartados correspondientes y no altera datos del curso.

## Actualización de navegación y perfiles

El inicio `/` incluye el formulario de acceso con entradas de Docente, Ayudante y Super admin. `/login` redirige al formulario del inicio.

- `/admin/dashboard`: directorio de profesores y ayudantes. Abrir una persona lleva a `/teacher/dashboard?profesor=ID`, que limita las asignaturas visibles a sus asignaciones. No se cambia el token ni se inicia sesión como esa persona: las operaciones mantienen al administrador como actor en la auditoría.
- Dentro de esa vista, «Gestionar asignaturas» permite crear/asignar cursos, editar sus datos y retirar accesos. La creación y asignación inicial se guarda en una sola operación de backend.
- `/assistant/dashboard`: vista de ayudante con el mismo flujo de evaluación. Puede editar parámetros, materiales, informes, preguntas, resultados, citas y su disponibilidad en los cursos asignados. La nómina es de solo lectura; agregar, importar, editar y retirar alumnos está prohibido en interfaz y API.
- La guía integrada destaca elementos reales y muestra explicaciones junto al control. Cambia de sección y desplaza la página siguiendo el flujo; los elementos destacados siguen siendo interactivos. Se puede avanzar, volver o salir sin modificar datos automáticamente.

Estas reglas reemplazan la restricción anterior de ayudante de solo consulta para toda la aplicación: ahora únicamente la gestión de alumnos es de solo lectura para ayudantes.

## Funciones operativas

Incluye recuperación de contraseña, historial de correos, avisos de citas, validación de agenda, cierre/archivo de evaluaciones, exportación CSV/PDF y cola persistente de PDF con reintentos. Ver [avance y configuración pendiente](../docs/AVANCE_FUNCIONALIDADES.md). SMTP e IA reales requieren configuración del servidor.

Para Gmail y Google Workspace, el superadministrador puede guardar la configuración, enviar una prueba y activar los envíos desde el panel. Ver [configuración de Gmail](../docs/CONFIGURAR_GMAIL.md). No se solicita la contraseña por chat ni se devuelve desde la API.
