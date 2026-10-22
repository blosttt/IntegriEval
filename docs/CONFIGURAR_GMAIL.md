# Configurar correo con Gmail o Google Workspace

La configuración está en **Superadmin → Configurar correo Gmail**. Solo una cuenta administrativa puede verla o modificarla.

## Preparar la cuenta

1. Elegir la cuenta de Gmail o Google Workspace que enviará los mensajes.
2. Activar la verificación en dos pasos y generar una **contraseña de aplicación** para IntegryEval. No se usa la contraseña normal de Google. La disponibilidad de esta opción depende de la configuración de seguridad y, en cuentas institucionales, de las políticas del administrador.
3. Consultar las instrucciones oficiales de [contraseñas de aplicación](https://support.google.com/accounts/answer/185833?hl=es) y [envío desde aplicaciones en Google Workspace](https://support.google.com/a/answer/176600?hl=es). Si la institución no permite contraseñas de aplicación, este flujo no evita esa restricción: será necesario acordar con TI un método autorizado, como OAuth o un relay institucional, que no se implementan en este panel.

## Configurar y probar

1. Ingresar a IntegryEval como superadministrador y abrir **Configurar correo Gmail**.
2. Completar la cuenta, su contraseña de aplicación y la URL de IntegryEval. El servidor es `smtp.gmail.com`; se puede elegir **587 con STARTTLS** o **465 con TLS**. El remitente se mantiene igual a la cuenta autenticada.
3. Guardar. La configuración se escribe atómicamente en el `.env` local y se aplica al proceso de la API. Una contraseña guardada no se devuelve al navegador ni aparece en auditoría. Al cambiar de cuenta se exige una contraseña nueva.
4. Enviar una prueba a una dirección elegida expresamente. El mensaje no contiene datos de alumnos. Para evitar repeticiones accidentales se admite una prueba por minuto por administrador.
5. Revisar la bandeja de entrada y spam. Que Gmail acepte el mensaje no garantiza que haya llegado a la bandeja de entrada.
6. Marcar **Confirmo que recibí el correo de prueba** y pulsar **Activar envíos**. No se puede activar sin una prueba aceptada para la configuración actual.

Al cambiar cuenta, contraseña, conexión o URL se desactivan los envíos y la prueba anterior deja de validar la nueva configuración. Si no se cambió la cuenta, dejar vacía la contraseña permite conservarla. También existe un botón para desactivar los envíos.

## Alcance y pendientes

- Las invitaciones Flash, recuperación de acceso, notificaciones y recordatorios utilizan la misma configuración segura.
- Las direcciones terminadas en `.invalid`, utilizadas en los datos demo, no reciben mensajes.
- No se reintentan automáticamente todos los correos históricos al activar SMTP. El docente puede reintentar los envíos que sigan vigentes desde el historial del curso.
- Una URL `localhost` solo se abre en el equipo donde corre IntegryEval. Para alumnos externos se necesita desplegar la aplicación o disponer de una dirección accesible para ellos.
- `.env` está excluido de Git; también lo están bases de datos, registros y archivos locales.
- Esta entrega se probó con SMTP simulado y validaciones de permisos, TLS, guardado y activación. No se ha enviado una prueba real de Gmail: falta que el usuario ingrese su cuenta y contraseña de aplicación en el panel y confirme la recepción.
