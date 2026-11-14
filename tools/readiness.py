from pathlib import Path
from urllib.parse import urlsplit
import time


def inspect_readiness(config):
    public = urlsplit(config.PUBLIC_APP_URL)
    backups = sorted(Path(config.BACKUP_DIR).glob('integrieval-*.backup.zip'), key=lambda item: item.stat().st_mtime, reverse=True)
    latest = backups[0] if backups else None
    backup_state = 'pendiente'
    missing = None
    if latest:
        from backend.app.services.backups import verify
        try:
            manifest = verify(latest)
            missing = len(manifest.get('missing_documents', []))
            backup_state = 'advertencia' if missing else 'verificado'
            if time.time() - latest.stat().st_mtime > config.BACKUP_INTERVAL_HOURS * 7200:
                backup_state = 'vencido'
        except Exception:
            backup_state = 'error'
    trained = Path(config.TESSDATA_PREFIX) if config.TESSDATA_PREFIX else None
    return {'environment': config.ENVIRONMENT, 'checks': [
        {'id': 'public_url', 'label': 'URL pública con HTTPS', 'ok': public.scheme == 'https' and public.hostname not in ('localhost', '127.0.0.1', '::1')},
        {'id': 'smtp', 'label': 'Correo configurado y activado', 'ok': bool(config.SMTP_ENABLED and config.SMTP_USER and config.SMTP_PASSWORD)},
        {'id': 'ia', 'label': 'Proveedor IA real configurado (requiere prueba de conexión)', 'ok': config.LLM_PROVIDER != 'mock' and (config.LLM_PROVIDER == 'ollama' or bool(config.LLM_API_KEY))},
        {'id': 'ocr', 'label': 'OCR habilitado con modelos instalados', 'ok': bool(config.OCR_ENABLED and trained and all((trained / (language + '.traineddata')).is_file() for language in config.OCR_LANGUAGE.split('+')))},
        {'id': 'demo', 'label': 'Cuentas demo desactivadas', 'ok': not config.SEED_DEMO_DATA},
        {'id': 'secret', 'label': 'Clave de sesión propia', 'ok': len(config.SECRET_KEY) >= 32 and config.SECRET_KEY != 'integrieval_super_secret_jwt_key_2026_info1197_secure_salt'},
        {'id': 'backup', 'label': 'Respaldo verificado y sin documentos faltantes', 'ok': backup_state == 'verificado'},
        {'id': 'automatic_backup', 'label': 'Respaldos automáticos habilitados', 'ok': config.BACKUP_ENABLED},
    ], 'backup': {'filename': latest.name if latest else None, 'state': backup_state, 'missing_documents': missing},
    'manual_checks': ['Recepción y acceso al enlace desde otro dispositivo', 'Calidad pedagógica revisada por docente', 'Prueba de carga representativa', 'Piloto integral autorizado']}
