from email.message import EmailMessage
import aiosmtplib
from backend.app.services.smtp_configuration import snapshot


def is_demo_recipient(recipient):
    return recipient.lower().rsplit('@',1)[-1].endswith('.invalid')


async def send_message(message:EmailMessage, config=None):
    config=config or snapshot()
    if not config['SMTP_USER'] or not config['SMTP_PASSWORD']:
        raise ValueError('SMTP no configurado')
    if config['SMTP_SECURITY'] not in ('starttls','tls'):
        raise ValueError('SMTP requiere TLS')
    return await aiosmtplib.send(message,hostname=config['SMTP_HOST'],port=config['SMTP_PORT'],
        username=config['SMTP_USER'],password=config['SMTP_PASSWORD'],
        use_tls=config['SMTP_SECURITY']=='tls',start_tls=config['SMTP_SECURITY']=='starttls',
        validate_certs=True,timeout=15)
