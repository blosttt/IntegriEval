import argparse
import getpass
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def configure(path, environment='development', url='http://127.0.0.1:3000', docker=False):
    from dotenv import dotenv_values, set_key
    path = Path(path).resolve()
    previous = dotenv_values(path) if path.exists() else {}
    production = environment == 'production'
    parsed = urlsplit(url)
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
        raise ValueError('Indica únicamente el origen de la aplicación, sin rutas ni credenciales')
    if production and (parsed.scheme != 'https' or parsed.hostname in ('localhost', '127.0.0.1', '::1')):
        raise ValueError('Producción requiere una URL HTTPS pública')
    if not production and parsed.scheme not in ('http', 'https'):
        raise ValueError('URL HTTP o HTTPS requerida')
    data = Path('/app/data') if docker else ROOT
    uploads = data / 'uploads'
    values = {
        'ENVIRONMENT': environment, 'PUBLIC_APP_URL': url.rstrip('/'),
        'SEED_DEMO_DATA': 'false' if production else 'true',
        'CORS_ORIGINS': url.rstrip('/') if production else 'http://127.0.0.1:3000,http://localhost:3000',
        'ALLOWED_HOSTS': f'{parsed.hostname},backend,localhost,127.0.0.1' if production else '127.0.0.1,localhost,testserver',
        'LLM_PROVIDER': 'ollama', 'LLM_MODEL': 'llama3.2:3b',
        'LLM_BASE_URL': 'http://ollama:11434' if docker else 'http://127.0.0.1:11434',
        'LLM_TIMEOUT_SECONDS': '180', 'APP_TIMEZONE': 'America/Santiago',
        'SMTP_ENABLED': 'false', 'SMTP_SECURITY': 'starttls', 'SMTP_PORT': '587',
        'BACKUP_ENABLED': 'true', 'BACKUP_KEEP': '7', 'BACKUP_INTERVAL_HOURS': '24',
        'DATABASE_URL': 'sqlite:////app/data/integrieval.db' if docker else 'sqlite:///' + str(data / 'integrieval.db').replace('\\', '/'),
        'UPLOAD_DIR': '/app/data/uploads' if docker else str(uploads),
        'MATERIALS_DIR': '/app/data/uploads/materiales' if docker else str(uploads / 'materiales'),
        'WORKS_DIR': '/app/data/uploads/trabajos' if docker else str(uploads / 'trabajos'),
        'BACKUP_DIR': '/app/backups' if docker else str(ROOT / 'backups'),
        'OCR_ENABLED': 'false', 'OCR_LANGUAGE': 'spa+eng',
        'TESSDATA_PREFIX': '/app/data/uploads/ocr' if docker else str(uploads / 'ocr'),
    }
    # Existing integration settings are preserved; intentional environment controls are applied.
    force = {'ENVIRONMENT', 'PUBLIC_APP_URL', 'SEED_DEMO_DATA', 'CORS_ORIGINS', 'ALLOWED_HOSTS'}
    updates = {key: value for key, value in values.items() if key not in previous or key in force}
    if previous.get('PUBLIC_APP_URL', '').rstrip('/') != url.rstrip('/'):
        updates['SMTP_ENABLED'] = 'false'
    if len(previous.get('SECRET_KEY') or '') < 32 or previous['SECRET_KEY'] == 'integrieval_super_secret_jwt_key_2026_info1197_secure_salt':
        updates['SECRET_KEY'] = secrets.token_urlsafe(48)
    if production and previous.get('LLM_PROVIDER') == 'mock':
        updates['LLM_PROVIDER'] = 'ollama'
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.setup-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            stream.write(path.read_text(encoding='utf-8') if path.exists() else '')
        for key, value in updates.items():
            set_key(temporary, key, str(value), quote_mode='always')
        os.replace(temporary, path)
        if os.name != 'nt':
            path.chmod(0o600)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {'configured': True, 'environment': environment, 'existing_secrets_preserved': True}


def install_ocr(folder):
    import hashlib
    import urllib.request
    revision = '87416418657359cb625c412a48b6e1d6d41c29bd'
    files = {'spa.traineddata': '6f2e04d02774a18f01bed44b1111f2cd7f3ba7ac9dc4373cd3f898a40ea6b464',
             'eng.traineddata': '7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2'}
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for name, expected in files.items():
        target = folder / name
        if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == expected:
            continue
        with urllib.request.urlopen(f'https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{revision}/{name}', timeout=60) as response:
            content = response.read(20 * 1024**2 + 1)
        if len(content) > 20 * 1024**2 or hashlib.sha256(content).hexdigest() != expected:
            raise ValueError('El modelo OCR no coincide con la distribución oficial verificada')
        descriptor, name_temp = tempfile.mkstemp(prefix='.ocr-', dir=folder)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(content)
            os.replace(name_temp, target)
        finally:
            Path(name_temp).unlink(missing_ok=True)
    return {'ocr': 'verified', 'languages': ['spa', 'eng']}


def create_admin(email, name):
    from pydantic import TypeAdapter, EmailStr
    from backend.app.database import Base, engine, SessionLocal, protect_audit_logs
    from backend.app import models
    from backend.app.auth import hash_password
    from backend.app.services.security import DEMO_EMAILS
    email = str(TypeAdapter(EmailStr).validate_python(email)).lower()
    if email in DEMO_EMAILS:
        raise ValueError('Usa una cuenta propia; las direcciones demo están reservadas')
    password = getpass.getpass('Contraseña nueva (no se muestra): ')
    if len(password) < 12 or len(password.encode()) > 72 or password != getpass.getpass('Repite la contraseña: '):
        raise ValueError('Usa al menos 12 caracteres, hasta 72 bytes UTF-8 y confirmación idéntica')
    Base.metadata.create_all(engine)
    from backend.app.migrations import upgrade_activities, upgrade_questions
    upgrade_activities(engine)
    upgrade_questions(engine)
    protect_audit_logs()
    with SessionLocal() as db:
        if db.query(models.Usuario).filter_by(correo=email).first():
            raise ValueError('La cuenta ya existe; no se cambia su contraseña')
        user = models.Usuario(nombre=name, correo=email, contrasena=hash_password(password), rol='admin')
        db.add(user)
        db.commit()
    return {'admin_created': True}


def main():
    parser = argparse.ArgumentParser(description='Instalación y mantenimiento de IntegryEval')
    parser.add_argument('--env-file', help='Archivo de configuración local; nunca se imprime su contenido')
    commands = parser.add_subparsers(dest='command', required=True)
    setup = commands.add_parser('configure')
    setup.add_argument('--environment', choices=['development', 'production'], default='development')
    setup.add_argument('--url', default='http://127.0.0.1:3000')
    setup.add_argument('--docker', action='store_true')
    commands.add_parser('doctor')
    commands.add_parser('ocr')
    backup = commands.add_parser('backup'); backup.add_argument('--destination')
    verify = commands.add_parser('verify'); verify.add_argument('archive')
    restore = commands.add_parser('restore'); restore.add_argument('archive'); restore.add_argument('--output', required=True)
    admin = commands.add_parser('create-admin'); admin.add_argument('--email', required=True); admin.add_argument('--name', required=True)
    args = parser.parse_args()
    if args.env_file:
        os.environ['INTEGRIEVAL_ENV_FILE'] = str(Path(args.env_file).resolve())
    try:
        if args.command == 'configure':
            result = configure(args.env_file or ROOT / '.env', args.environment, args.url, args.docker)
        elif args.command in ('verify', 'restore'):
            from backend.app.services.backups import verify, restore
            if args.command == 'verify':
                manifest = verify(args.archive)
                result = {'verified': True, 'files': len(manifest['files']), 'missing_documents': len(manifest.get('missing_documents', []))}
            else:
                result = restore(args.archive, args.output)
        elif args.command == 'create-admin':
            result = create_admin(args.email, args.name)
        else:
            from backend.app.config import settings
            if args.command == 'backup':
                from backend.app.services.backups import snapshot
                result = snapshot(settings, args.destination)
            elif args.command == 'ocr':
                from dotenv import set_key
                from backend.app.config import ENV_PATH
                result = install_ocr(settings.TESSDATA_PREFIX or settings.UPLOAD_DIR / 'ocr')
                set_key(str(ENV_PATH), 'TESSDATA_PREFIX', str(settings.TESSDATA_PREFIX or settings.UPLOAD_DIR / 'ocr'))
                set_key(str(ENV_PATH), 'OCR_ENABLED', 'true')
            else:
                from tools.readiness import inspect_readiness
                result = inspect_readiness(settings)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        # Validation exceptions may contain secret input values; never dump them.
        from pydantic import ValidationError
        message = 'Configuración inválida: revisa los campos requeridos para el entorno.' if isinstance(error, ValidationError) else str(error)
        print(json.dumps({'error': message}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
