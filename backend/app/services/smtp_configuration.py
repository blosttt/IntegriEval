"""Atomic local configuration. Secrets never appear in API or audit responses."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
from threading import RLock
from dotenv import set_key
from backend.app.config import BASE_DIR, settings

ENV_PATH = BASE_DIR / '.env'
LOCK = RLock()
CONFIG_KEYS = ('SMTP_HOST','SMTP_PORT','SMTP_SECURITY','SMTP_USER','SMTP_PASSWORD','SMTP_FROM','PUBLIC_APP_URL')


def snapshot():
    with LOCK:
        return {key:getattr(settings,key) for key in (*CONFIG_KEYS,'SMTP_ENABLED')}


def fingerprint(values=None):
    values = values or snapshot()
    data=json.dumps({key:values[key] for key in CONFIG_KEYS},sort_keys=True).encode()
    return hmac.new(settings.SECRET_KEY.encode(),data,hashlib.sha256).hexdigest()


def persist(values):
    with LOCK:
        path=Path(ENV_PATH)
        descriptor,name=tempfile.mkstemp(prefix='.smtp-',suffix='.tmp',dir=path.parent)
        try:
            with os.fdopen(descriptor,'w',encoding='utf-8',newline='') as output:
                output.write(path.read_text(encoding='utf-8') if path.exists() else '')
            for key,value in values.items():
                set_key(name,key,str(value).lower() if isinstance(value,bool) else str(value),quote_mode='always')
            os.replace(name,path)
            for key,value in values.items():
                setattr(settings,key,value)
        finally:
            Path(name).unlink(missing_ok=True)
