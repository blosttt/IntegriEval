import logging
from html import escape
from email.message import EmailMessage
import aiosmtplib
from backend.app.config import settings

logger = logging.getLogger(__name__)

async def send_flash_test_email(
    student_name: str,
    student_email: str,
    course_name: str,
    test_link: str,
    validity_hours: int = 48,
    seconds_per_question: int = 60
) -> bool:
    """
    Sends Flash Test invitation email via Gmail SMTP TLS (RF-010, RI-002).
    If SMTP credentials are not configured, logs link and simulates successful dispatch.
    """
    subject = f"IntegriEval — Verificación Oral Flash: {course_name}".replace("\r", " ").replace("\n", " ")
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
        <p>Estimado/a <strong>{escape(student_name)}</strong>,</p>
        <p>Como parte del proceso de evaluación de su entrega en la asignatura <strong>{escape(course_name)}</strong>, debe completar una breve verificación oral/flash interactiva.</p>
        
        <div class="alert">
          <strong>Reglas del Test:</strong>
          <ul style="margin: 6px 0 0 0; padding-left: 20px;">
            <li>El enlace es de <strong>uso único</strong> y expira en {validity_hours} horas.</li>
            <li>Cuenta con un temporizador activo ({seconds_per_question} segundos por pregunta).</li>
            <li>Si el tiempo expira, sus respuestas parciales serán registradas automáticamente.</li>
          </ul>
        </div>

        <p style="text-align: center;">
          <a href="{escape(test_link)}" class="btn" target="_blank">Iniciar Flash Test Ahora</a>
        </p>

        <p style="font-size: 13px; color: #475569;">
          Si el botón no funciona, copie y pegue el siguiente enlace en su navegador:<br>
          <a href="{escape(test_link)}" style="color: #2563eb; word-break: break-all;">{escape(test_link)}</a>
        </p>

        <div class="footer">
          <p>IntegriEval — INFO1197 Septiembre 2026. Sistema de Verificación Académica y Supervisión Docente.</p>
        </div>
      </div>
    </body>
    </html>
    """

    from backend.app.services.smtp_configuration import snapshot
    from backend.app.services.smtp_transport import send_message, is_demo_recipient
    current=snapshot()
    if is_demo_recipient(student_email) or not current['SMTP_ENABLED'] or not current['SMTP_USER'] or not current['SMTP_PASSWORD']:
        logger.info("Correo Flash no enviado: SMTP desactivado o destinatario de demostración")
        return False

    message = EmailMessage()
    message["From"] = current['SMTP_FROM'] or current['SMTP_USER']
    message["To"] = student_email
    message["Subject"] = subject
    message.set_content(
        f"Hola {student_name},\n\nPara completar tu verificación en {course_name}, ingresa al siguiente enlace:\n{test_link}\n\nVálido por {validity_hours}h."
    )
    message.add_alternative(html_content, subtype="html")

    try:
        rejected,_ = await send_message(message,current)
        if rejected:return False
        return True
    except Exception as e:
        logger.error("No se pudo enviar el correo Flash (%s)",type(e).__name__)
        return False
