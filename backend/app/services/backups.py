"""Verified SQLite snapshots and offline, non-overwriting restoration."""
import asyncio
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import tempfile
import threading
from datetime import datetime, timezone
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED

LOCK = threading.Lock()


def database_path(config):
    from sqlalchemy.engine import make_url
    url = make_url(config.DATABASE_URL)
    if url.get_backend_name() != 'sqlite' or not url.database or url.database == ':memory:':
        raise ValueError('El respaldo integrado admite bases SQLite almacenadas en disco')
    return Path(url.database).resolve()


def roots(config):
    return {'materiales': Path(config.MATERIALS_DIR).resolve(),
            'trabajos': Path(config.WORKS_DIR).resolve(),
            'queue': (Path(config.UPLOAD_DIR) / 'queue').resolve()}


def digest_file(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def snapshot(config, destination=None):
    with LOCK:
        source = database_path(config)
        if not source.is_file():
            raise ValueError('La base de datos todavía no existe')
        folder = Path(destination or config.BACKUP_DIR).resolve()
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        name = f'integrieval-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}.backup.zip'
        target = folder / name
        with tempfile.TemporaryDirectory(prefix='.backup-', dir=folder) as temp:
            temp = Path(temp)
            db_copy = temp / 'database.sqlite3'
            with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as original, closing(sqlite3.connect(db_copy)) as copied:
                original.backup(copied)
                copied.commit()
            documents = {}
            path_map, missing = {}, []
            allowed = roots(config)
            with closing(sqlite3.connect(db_copy)) as db:
                if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('La base de datos no superó la comprobación de integridad')
                tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                for table, column in [('materiales', 'file_path'), ('trabajos', 'pdf_path'), ('upload_jobs', 'file_path')]:
                    if table not in tables:
                        continue
                    for (value,) in db.execute(f'SELECT {column} FROM {table} WHERE {column} IS NOT NULL'):
                        path = Path(value).resolve()
                        category = next((key for key, root in allowed.items() if path.is_relative_to(root)), None)
                        if not category or not path.is_file():
                            missing.append({'table': table, 'path': value})
                            continue
                        arc = 'documents/' + category + '/' + path.relative_to(allowed[category]).as_posix()
                        if path.is_symlink():
                            raise ValueError('No se admiten enlaces simbólicos en los documentos')
                        documents[arc] = path
                        path_map[value] = arc
            manifest = {'version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
                        'files': [], 'path_map': path_map, 'missing_documents': missing}
            files = {'database.sqlite3': db_copy, **documents}
            temporary_archive = temp / name
            with ZipFile(temporary_archive, 'w', ZIP_DEFLATED) as archive:
                for arc, path in files.items():
                    archive.write(path, arc)
                    manifest['files'].append({'name': arc, 'size': path.stat().st_size, 'sha256': digest_file(path)})
                archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False))
            verify(temporary_archive)
            os.replace(temporary_archive, target)
            if os.name != 'nt':
                target.chmod(0o600)
        # Retention only removes our older archives after a new archive verifies successfully.
        archives = sorted(folder.glob('integrieval-*.backup.zip'), key=lambda item: item.stat().st_mtime, reverse=True)
        for old in archives[config.BACKUP_KEEP:]:
            if old.parent == folder and not old.is_symlink():
                old.unlink()
        return {'filename': name, 'documents': len(documents), 'missing_documents': len(missing)}


def safe_name(name):
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and '..' not in path.parts and '\\' not in name and ':' not in name


def verify(path):
    with ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)) or len(names) > 100000 or any(not safe_name(name) for name in names):
            raise ValueError('Archivo de respaldo con rutas inválidas o duplicadas')
        if sum(entry.file_size for entry in entries) > 50 * 1024**3:
            raise ValueError('El respaldo excede el límite de 50 GB')
        if archive.getinfo('manifest.json').file_size > 5 * 1024**2:
            raise ValueError('Manifiesto demasiado extenso')
        manifest = json.loads(archive.read('manifest.json'))
        files = manifest.get('files', [])
        if manifest.get('version') != 1 or {item['name'] for item in files} | {'manifest.json'} != set(names) or len(files) + 1 != len(names):
            raise ValueError('El manifiesto no corresponde al contenido del respaldo')
        if 'database.sqlite3' not in names or any(item['name'] != 'database.sqlite3' and not item['name'].startswith(('documents/materiales/', 'documents/trabajos/', 'documents/queue/')) for item in files):
            raise ValueError('Contenido no admitido en el respaldo')
        for item in files:
            with archive.open(item['name']) as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            if actual != item['sha256'] or archive.getinfo(item['name']).file_size != item['size']:
                raise ValueError('El respaldo está corrupto o fue modificado')
        return manifest


def restore(path, output):
    """Create a separate data directory; never replace a running database."""
    import shutil
    manifest = verify(path)
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('La carpeta de restauración debe ser nueva; no se sobrescriben datos')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.restore-', dir=output.parent) as temporary:
        stage = Path(temporary)
        mappings = {}
        with ZipFile(path) as archive:
            for item in manifest['files']:
                name = item['name']
                relative = 'integrieval.db' if name == 'database.sqlite3' else 'uploads/' + name.removeprefix('documents/')
                target = stage / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(name) as source, target.open('wb') as destination:
                    shutil.copyfileobj(source, destination)
                mappings[name] = str(output / relative)
        database = stage / 'integrieval.db'
        with closing(sqlite3.connect(database)) as db, db:
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('La base restaurada no supera la comprobación de integridad')
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for table, column in [('materiales', 'file_path'), ('trabajos', 'pdf_path'), ('upload_jobs', 'file_path')]:
                if table in tables:
                    for original, arc in manifest.get('path_map', {}).items():
                        if arc not in mappings:
                            raise ValueError('Referencia de documento inválida en el manifiesto')
                        db.execute(f'UPDATE {table} SET {column}=? WHERE {column}=?', (mappings[arc], original))
            if 'password_resets' in tables:
                db.execute('UPDATE password_resets SET used=1')
            if 'mail_deliveries' in tables:
                db.execute("UPDATE mail_deliveries SET status='cancelled', error='Restauración: revisar antes de reenviar' WHERE status IN ('pending','running')")
            if 'upload_jobs' in tables:
                db.execute("UPDATE upload_jobs SET status='failed', error='Restauración: revisar y reintentar' WHERE status IN ('pending','running')")
            if 'smtp_verification' in tables:
                db.execute('DELETE FROM smtp_verification')
            if 'usuarios' in tables and 'credential_versions' in tables:
                db.execute('INSERT OR IGNORE INTO credential_versions (usuario_id,version) SELECT id,0 FROM usuarios')
                db.execute('UPDATE credential_versions SET version=version+1')
        output.mkdir(mode=0o700)
        try:
            for child in stage.iterdir():
                shutil.move(str(child), str(output / child.name))
        except Exception:
            # Keep partial data for inspection; a live database has never been touched.
            raise
    return {'database': str(output / 'integrieval.db'), 'missing_documents': len(manifest.get('missing_documents', []))}


async def backup_loop(config):
    import logging
    while True:
        try:
            await asyncio.to_thread(snapshot, config)
        except Exception:
            logging.getLogger(__name__).exception('No se pudo crear el respaldo automático')
        await asyncio.sleep(config.BACKUP_INTERVAL_HOURS * 3600)
