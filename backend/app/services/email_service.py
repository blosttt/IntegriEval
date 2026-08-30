"""
Email service using Gmail SMTP (free for MVP).
Requires: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL in .env
"""
import asyncio
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.database import settings


async def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Low-level async email sender via Gmail SMTP."""
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        print(f"[email_service] SMTP not configured. Would have sent '{subject}' to {to_email}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.FROM_EMAIL or settings.SMTP_USER
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            start_tls=True,
        )
        print(f"[email_service] Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"[email_service] Error sending email to {to_email}: {e}")
        return False


def send_flash_test_email_sync(
    student_email: str,
    student_name: str,
    eval_title: str,
    flash_token: str,
    ttl_hours: int,
) -> bool:
    """
    Sends the flash test invitation email synchronously (for use in background tasks).
    """
    flash_url = f"{settings.FRONTEND_URL}/flash/{flash_token}"
    subject = f"IntegriEval — Flash Test: {eval_title}"

    html_body = f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px;
              padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

    <h2 style="color: #1a1a2e; margin-bottom: 4px;">IntegriEval</h2>
    <p style="color: #666; margin-top: 0;">Verificación de autoría académica</p>

    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">

    <p>Hola <strong>{student_name}</strong>,</p>

    <p>Tu trabajo para la evaluación <strong>"{eval_title}"</strong> ha sido revisado.
    Como parte del proceso de verificación de autoría, debes completar un
    <strong>Flash Test</strong> con preguntas sobre tu propio trabajo.</p>

    <p>El test es <strong>cronometrado</strong>. Lee cada pregunta con atención y responde
    según lo que escribiste en tu informe.</p>

    <div style="text-align: center; margin: 32px 0;">
      <a href="{flash_url}"
         style="background: #4f46e5; color: white; padding: 14px 32px; border-radius: 6px;
                text-decoration: none; font-size: 16px; font-weight: bold;">
        Iniciar Flash Test →
      </a>
    </div>

    <p style="color: #888; font-size: 13px;">
      Este enlace es personal e intransferible. Expira en <strong>{ttl_hours} horas</strong>.
      Si no puedes acceder, contacta a tu profesor.
    </p>

    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
    <p style="color: #aaa; font-size: 12px; text-align: center;">
      IntegriEval — Sistema de verificación de integridad académica
    </p>
  </div>
</body>
</html>
"""
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_send_email(student_email, subject, html_body))
        loop.close()
        return result
    except Exception as e:
        print(f"[email_service] Sync send error: {e}")
        return False


def send_appointment_email_sync(
    student_email: str,
    student_name: str,
    eval_title: str,
    professor_name: str,
    scheduled_time_str: str,
    appointment_type: str,
    notes: str = "",
) -> bool:
    """
    Sends an appointment notification email to the student.
    """
    type_labels = {
        "defense": "Defensa oral — Justificación de resultados",
        "high_score_verification": "Verificación de excelencia",
        "random_verification": "Revisión de verificación aleatoria",
    }
    type_label = type_labels.get(appointment_type, "Reunión de revisión")

    subject = f"IntegriEval — Convocatoria: {eval_title}"

    html_body = f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px;
              padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

    <h2 style="color: #1a1a2e; margin-bottom: 4px;">IntegriEval</h2>
    <p style="color: #666; margin-top: 0;">Convocatoria a revisión presencial</p>

    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">

    <p>Hola <strong>{student_name}</strong>,</p>

    <p>Has sido convocado/a a una reunión de revisión para la evaluación
    <strong>"{eval_title}"</strong>.</p>

    <table style="width: 100%; border-collapse: collapse; margin: 24px 0;">
      <tr>
        <td style="padding: 10px; background: #f9f9f9; font-weight: bold; width: 40%;">
          Tipo de revisión
        </td>
        <td style="padding: 10px; background: #f9f9f9;">{type_label}</td>
      </tr>
      <tr>
        <td style="padding: 10px; font-weight: bold;">Profesor</td>
        <td style="padding: 10px;">{professor_name}</td>
      </tr>
      <tr>
        <td style="padding: 10px; background: #f9f9f9; font-weight: bold;">
          Fecha y hora
        </td>
        <td style="padding: 10px; background: #f9f9f9;">
          <strong>{scheduled_time_str}</strong>
        </td>
      </tr>
      {"<tr><td style='padding:10px;font-weight:bold;'>Notas</td><td style='padding:10px;'>" + notes + "</td></tr>" if notes else ""}
    </table>

    <p>En esta reunión tendrás la oportunidad de <strong>justificar tu trabajo</strong>
    y potencialmente mejorar tu calificación.</p>

    <p style="color: #888; font-size: 13px;">
      Si tienes algún inconveniente con el horario, comunícate con tu profesor a la brevedad.
    </p>

    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
    <p style="color: #aaa; font-size: 12px; text-align: center;">
      IntegriEval — Sistema de verificación de integridad académica
    </p>
  </div>
</body>
</html>
"""
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_send_email(student_email, subject, html_body))
        loop.close()
        return result
    except Exception as e:
        print(f"[email_service] Sync send error: {e}")
        return False
