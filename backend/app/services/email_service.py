import logging
from email.message import EmailMessage
import aiosmtplib
from backend.app.config import settings

logger = logging.getLogger(__name__)

async def send_flash_test_email(
    student_name: str,
    student_email: str,
    course_name: str,
    test_link: str,
    validity_hours: int = 48
) -> bool:
    """
    Sends Flash Test invitation email via Gmail SMTP TLS (RF-010, RI-002).
    If SMTP credentials are not configured, logs link and simulates successful dispatch.
    """
    subject = f"IntegriEval — Verificación Oral Flash: {course_name}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 20px; color: #1a202c; }}
        .card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
        .header {{ border-bottom: 2px solid #3b82f6; padding-bottom: 16px; margin-bottom: 24px; }}
        .badge {{ background: #eff6ff; color: #1d4ed8; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .btn {{ display: inline-block; background: #2563eb; color: #ffffff !important; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 20px 0; }}
        .footer {{ margin-top: 24px; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 16px; }}
        .alert {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; margin: 16px 0; font-size: 14px; color: #92400e; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <span class="badge">IntegriEval • Evaluación Auténtica</span>
          <h2 style="margin: 8px 0 0 0; color: #0f172a;">Verificación Flash de Integridad</h2>
        </div>
        <p>Estimado/a <strong>{student_name}</strong>,</p>
        <p>Como parte del proceso de evaluación de su entrega en la asignatura <strong>{course_name}</strong>, debe completar una breve verificación oral/flash interactiva.</p>
        
        <div class="alert">
          <strong>Reglas del Test:</strong>
          <ul style="margin: 6px 0 0 0; padding-left: 20px;">
            <li>El enlace es de <strong>uso único</strong> y expira en {validity_hours} horas.</li>
            <li>Cuenta con un temporizador activo (60 segundos por pregunta/test).</li>
            <li>Si el tiempo expira, sus respuestas parciales serán registradas automáticamente.</li>
          </ul>
        </div>

        <p style="text-align: center;">
          <a href="{test_link}" class="btn" target="_blank">Iniciar Flash Test Ahora</a>
        </p>

        <p style="font-size: 13px; color: #475569;">
          Si el botón no funciona, copie y pegue el siguiente enlace en su navegador:<br>
          <a href="{test_link}" style="color: #2563eb; word-break: break-all;">{test_link}</a>
        </p>

        <div class="footer">
          <p>IntegriEval — INFO1197 Septiembre 2026. Sistema de Verificación Académica y Supervisión Docente.</p>
        </div>
      </div>
    </body>
    </html>
    """

    if not settings.SMTP_ENABLED or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info(f"[SIMULADOR SMTP] Despacho Flash Test a {student_email}: {test_link}")
        return True

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM or settings.SMTP_USER
    message["To"] = student_email
    message["Subject"] = subject
    message.set_content(
        f"Hola {student_name},\n\nPara completar tu verificación en {course_name}, ingresa al siguiente enlace:\n{test_link}\n\nVálido por {validity_hours}h."
    )
    message.add_alternative(html_content, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=True,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            timeout=10.0
        )
        return True
    except Exception as e:
        logger.error(f"Error enviando correo a {student_email} vía SMTP: {e}")
        return False
