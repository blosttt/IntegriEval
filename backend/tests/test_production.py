import asyncio
import json
import sqlite3
from types import SimpleNamespace
from zipfile import ZipFile
import pytest
from dotenv import dotenv_values
from backend.app.config import Settings, settings
from backend.app.auth import create_access_token
from backend.app.services import security, backups


def production(**overrides):
    values = dict(ENVIRONMENT='production', SECRET_KEY='S' * 48, SEED_DEMO_DATA=False,
                  PUBLIC_APP_URL='https://integrieval.example.org', CORS_ORIGINS='https://integrieval.example.org',
                  ALLOWED_HOSTS='integrieval.example.org,backend,localhost', LLM_PROVIDER='ollama')
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.mark.parametrize('overrides', [
    {'SECRET_KEY': 'short'}, {'SECRET_KEY': Settings.model_fields['SECRET_KEY'].default},
    {'SEED_DEMO_DATA': True}, {'LLM_PROVIDER': 'mock'}, {'PUBLIC_APP_URL': 'http://integrieval.example.org'},
    {'CORS_ORIGINS': '*'}, {'ALLOWED_HOSTS': '*'}, {'ALLOWED_HOSTS': 'localhost'},
    {'PUBLIC_APP_URL': 'https://user:password@integrieval.example.org'}, {'BACKUP_KEEP': 1},
])
def test_production_rejects_insecure_configuration(overrides):
    with pytest.raises(ValueError):
        production(**overrides)


def test_valid_production_config():
    config = production()
    assert not config.SEED_DEMO_DATA
    assert config.cors_origins == ['https://integrieval.example.org']


def test_login_limit_persists_and_cannot_be_bypassed_with_forwarded_header(client, monkeypatch):
    monkeypatch.setattr(security.time, 'time', lambda: 1800000000)
    data = {'correo': 'nonexistent@example.org', 'contrasena': 'WrongPassword!'}
    for _ in range(8):
        assert client.post('/api/auth/login', json=data).status_code == 401
    denied = client.post('/api/auth/login', json=data, headers={'X-Forwarded-For': '203.0.113.100'})
    assert denied.status_code == 429 and int(denied.headers['retry-after']) > 0
    monkeypatch.setattr(security.time, 'time', lambda: 1800000901)
    assert client.post('/api/auth/login', json=data).status_code == 401


def test_forgot_password_is_rate_limited(client):
    for _ in range(10):
        assert client.post('/api/auth/forgot-password', json={'correo': 'nobody@example.org'}).status_code == 200
    assert client.post('/api/auth/forgot-password', json={'correo': 'nobody@example.org'}).status_code == 429


def test_demo_token_and_login_disabled_without_destroying_account(client, db_session, monkeypatch):
    from backend.app import models as m
    from backend.app.auth import hash_password
    user = m.Usuario(nombre='Demo', correo='admin@universidad.cl', contrasena=hash_password('Admin123!'), rol='admin')
    db_session.add(user); db_session.commit()
    token = create_access_token({'sub': str(user.id)})
    monkeypatch.setattr(settings, 'SEED_DEMO_DATA', False)
    assert client.get('/api/auth/me', headers={'Authorization': 'Bearer ' + token}).status_code == 401
    assert client.post('/api/auth/login', json={'correo': user.correo, 'contrasena': 'Admin123!'}).status_code == 401
    assert db_session.get(m.Usuario, user.id) is not None


def test_cors_and_security_headers(client):
    good = client.options('/api/auth/me', headers={'Origin': settings.cors_origins[0], 'Access-Control-Request-Method': 'GET', 'Access-Control-Request-Headers': 'authorization'})
    assert good.status_code == 200
    assert good.headers['access-control-allow-origin'] == settings.cors_origins[0]
    bad = client.options('/api/auth/me', headers={'Origin': 'https://untrusted.example.org', 'Access-Control-Request-Method': 'GET'})
    assert bad.status_code == 400 and 'access-control-allow-origin' not in bad.headers
    response = client.get('/api/auth/me')
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['referrer-policy'] == 'no-referrer'
    assert response.headers['x-content-type-options'] == 'nosniff'


def test_websocket_rejects_credentials_in_url(client, seeded_teacher):
    from starlette.websockets import WebSocketDisconnect
    teacher, course = seeded_teacher['teacher'], seeded_teacher['course']
    token = create_access_token({'sub': str(teacher.id)})
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f'/ws/panel/{course.id}?token={token}'):
            pass


def test_configurator_generates_unique_key_and_preserves_secrets(tmp_path):
    from tools.manage import configure
    path = tmp_path / '.env'
    configure(path)
    first = dotenv_values(path)
    assert len(first['SECRET_KEY']) >= 32
    path.write_text(path.read_text() + "SMTP_USER='private@example.org'\nSMTP_PASSWORD='private-test-value'\n", encoding='utf-8')
    configure(path)
    second = dotenv_values(path)
    assert second['SECRET_KEY'] == first['SECRET_KEY']
    assert second['SMTP_PASSWORD'] == 'private-test-value'
    prod_path = tmp_path / '.env.production'
    configure(prod_path, 'production', 'https://integrieval.example.org', docker=True)
    assert Settings(_env_file=None, **dotenv_values(prod_path)).ENVIRONMENT == 'production'


def test_configurator_replaces_weak_demo_configuration(tmp_path):
    from tools.manage import configure
    path = tmp_path / '.env'
    path.write_text("SECRET_KEY='short'\nLLM_PROVIDER='mock'\n", encoding='utf-8')
    configure(path, 'production', 'https://integrieval.example.org')
    configured = dotenv_values(path)
    assert len(configured['SECRET_KEY']) >= 32
    assert configured['LLM_PROVIDER'] == 'ollama'
    assert Settings(_env_file=None, **configured).SEED_DEMO_DATA is False


def test_ocr_installer_rejects_unverified_download(tmp_path, monkeypatch):
    import io
    import urllib.request
    from tools.manage import install_ocr
    monkeypatch.setattr(urllib.request, 'urlopen', lambda *args, **kwargs: io.BytesIO(b'invalid-model'))
    with pytest.raises(ValueError):
        install_ocr(tmp_path/'ocr')
    assert not list((tmp_path/'ocr').glob('*.traineddata'))


@pytest.fixture
def backup_config(tmp_path):
    upload = tmp_path / 'uploads'
    doc = upload / 'materiales' / 'sample.txt'
    doc.parent.mkdir(parents=True); doc.write_text('Documento académico', encoding='utf-8')
    database = tmp_path / 'original.db'
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE materiales (file_path TEXT)')
        db.execute('INSERT INTO materiales VALUES (?)', (str(doc),))
        db.execute('CREATE TABLE usuarios (id INTEGER PRIMARY KEY)')
        db.execute('INSERT INTO usuarios VALUES (1)')
        db.execute('CREATE TABLE credential_versions (usuario_id INTEGER PRIMARY KEY, version INTEGER)')
        db.execute('CREATE TABLE password_resets (used INTEGER)')
        db.execute('INSERT INTO password_resets VALUES (0)')
        db.execute('CREATE TABLE mail_deliveries (status TEXT, error TEXT)')
        db.execute("INSERT INTO mail_deliveries VALUES ('pending', NULL)")
        db.execute('CREATE TABLE smtp_verification (id INTEGER)')
        db.execute('INSERT INTO smtp_verification VALUES (1)')
    return SimpleNamespace(DATABASE_URL='sqlite:///' + str(database), UPLOAD_DIR=upload,
        MATERIALS_DIR=upload/'materiales', WORKS_DIR=upload/'trabajos', BACKUP_DIR=tmp_path/'backups', BACKUP_KEEP=2)


def test_backup_roundtrip_rebases_documents_and_revokes_pending_credentials(backup_config, tmp_path):
    config = backup_config
    result = backups.snapshot(config)
    archive = config.BACKUP_DIR / result['filename']
    assert result['documents'] == 1 and result['missing_documents'] == 0
    assert len(backups.verify(archive)['files']) == 2
    output = tmp_path / 'restored'
    restored = backups.restore(archive, output)
    with sqlite3.connect(restored['database']) as db:
        path = db.execute('SELECT file_path FROM materiales').fetchone()[0]
        from pathlib import Path
        assert Path(path).read_text(encoding='utf-8') == 'Documento académico'
        assert str(output) in path
        assert db.execute('SELECT version FROM credential_versions').fetchone()[0] == 1
        assert db.execute('SELECT used FROM password_resets').fetchone()[0] == 1
        assert db.execute('SELECT status FROM mail_deliveries').fetchone()[0] == 'cancelled'
        assert db.execute('SELECT count(*) FROM smtp_verification').fetchone()[0] == 0
    with pytest.raises(ValueError):
        backups.restore(archive, output)
    with sqlite3.connect(backups.database_path(config)) as db:
        assert db.execute('SELECT used FROM password_resets').fetchone()[0] == 0


def test_backup_detects_corruption_and_unsafe_paths(backup_config, tmp_path):
    result = backups.snapshot(backup_config)
    original = backup_config.BACKUP_DIR / result['filename']
    corrupted = tmp_path / 'corrupted.zip'
    with ZipFile(original) as source, ZipFile(corrupted, 'w') as target:
        for name in source.namelist():
            target.writestr(name, b'modified' if name.endswith('sample.txt') else source.read(name))
    with pytest.raises(ValueError):
        backups.verify(corrupted)
    attack = tmp_path / 'attack.zip'
    with ZipFile(attack, 'w') as archive:
        archive.writestr('../outside.txt', 'unsafe')
    with pytest.raises(ValueError):
        backups.restore(attack, tmp_path / 'unsafe-restore')
    assert not (tmp_path / 'outside.txt').exists()


def test_backup_retention_and_missing_files_are_visible(backup_config):
    config = backup_config
    with sqlite3.connect(backups.database_path(config)) as db:
        db.execute('INSERT INTO materiales VALUES (?)', (str(config.MATERIALS_DIR/'missing.pdf'),))
    for _ in range(3):
        result = backups.snapshot(config)
        assert result['missing_documents'] == 1
    assert len(list(config.BACKUP_DIR.glob('*.backup.zip'))) == 2


def test_readiness_is_admin_only(client, seeded_teacher, seeded_admin, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'BACKUP_DIR', tmp_path/'backups')
    teacher_token = create_access_token({'sub': str(seeded_teacher['teacher'].id)})
    admin_token = create_access_token({'sub': str(seeded_admin.id)})
    assert client.get('/api/admin/preparacion', headers={'Authorization':'Bearer '+teacher_token}).status_code == 403
    assert client.post('/api/admin/respaldos', headers={'Authorization':'Bearer '+teacher_token}).status_code == 403
    response = client.get('/api/admin/preparacion', headers={'Authorization':'Bearer '+admin_token})
    assert response.status_code == 200
    assert 'SMTP_PASSWORD' not in json.dumps(response.json())
    assert response.json()['backup']['state'] == 'pendiente'


def test_restored_database_cannot_resume_unverified_email(db_session, monkeypatch):
    from backend.app import models
    from backend.app.services.smtp_configuration import disable_unverified_mail, fingerprint
    monkeypatch.setattr(settings, 'SMTP_ENABLED', True)
    disable_unverified_mail(db_session)
    assert settings.SMTP_ENABLED is False
    db_session.add(models.SmtpVerification(id=1, config_hash=fingerprint(), recipient='test@example.org'))
    db_session.commit()
    monkeypatch.setattr(settings, 'SMTP_ENABLED', True)
    disable_unverified_mail(db_session)
    assert settings.SMTP_ENABLED is True


def test_isolated_load_test_does_not_touch_real_database():
    from tools.loadtest import benchmark
    result = asyncio.run(benchmark(users=3, concurrency=2))
    assert result['errors'] == 0 and result['requests'] == 18
