import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from urllib.parse import urlsplit

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = Path(os.environ.get("INTEGRIEVAL_ENV_FILE", str(BASE_DIR / ".env")))

class Settings(BaseSettings):
    PROJECT_NAME: str = "IntegriEval"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    SEED_DEMO_DATA: bool = True
    CORS_ORIGINS: str = "http://127.0.0.1:3000,http://localhost:3000"
    ALLOWED_HOSTS: str = "127.0.0.1,localhost,testserver"
    BACKUP_ENABLED: bool = False
    BACKUP_DIR: Path = BASE_DIR / "backups"
    BACKUP_INTERVAL_HOURS: int = 24
    BACKUP_KEEP: int = 7
    
    # Security (RNF-004, RNF-005)
    SECRET_KEY: str = "integrieval_super_secret_jwt_key_2026_info1197_secure_salt"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    BCRYPT_ROUNDS: int = 12  # RNF-005: bcrypt con factor >= 12
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/integrieval.db"
    
    # Upload Directories
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MATERIALS_DIR: Path = BASE_DIR / "uploads" / "materiales"
    WORKS_DIR: Path = BASE_DIR / "uploads" / "trabajos"
    
    # Gmail SMTP (RF-010, RI-002)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_SECURITY: str = "starttls"  # starttls (587) or tls (465)
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "integrieval@gmail.com"
    SMTP_ENABLED: bool = False
    PUBLIC_APP_URL: str = "http://127.0.0.1:3000"
    APP_TIMEZONE: str = "America/Santiago"
    OCR_ENABLED: bool = False
    OCR_LANGUAGE: str = "spa+eng"
    TESSDATA_PREFIX: str = ""
    
    # LLM Settings (RI-001, RF-014, RNF-007)
    LLM_PROVIDER: str = "mock"  # mock, ollama, openai, anthropic
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "http://localhost:11434"  # Default for Ollama
    LLM_MODEL: str = "llama3.2"
    LLM_TIMEOUT_SECONDS: float = 180.0
    
    # Host and Port
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    model_config = SettingsConfigDict(env_file=ENV_PATH, extra="ignore")

    @property
    def cors_origins(self):
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]

    @property
    def allowed_hosts(self):
        return [host.strip() for host in self.ALLOWED_HOSTS.split(',') if host.strip()]

    @model_validator(mode="after")
    def validate_production(self):
        if not 1 <= self.BACKUP_INTERVAL_HOURS <= 168 or not 2 <= self.BACKUP_KEEP <= 90:
            raise ValueError("Los respaldos requieren intervalo de 1 a 168 horas y retención de 2 a 90 copias")
        if self.ENVIRONMENT not in {"development", "test", "production"}:
            raise ValueError("ENVIRONMENT debe ser development, test o production")
        if self.ENVIRONMENT == "production":
            url = urlsplit(self.PUBLIC_APP_URL)
            if len(self.SECRET_KEY) < 32 or self.SECRET_KEY == "integrieval_super_secret_jwt_key_2026_info1197_secure_salt":
                raise ValueError("Producción requiere una SECRET_KEY propia de al menos 32 caracteres")
            if self.SEED_DEMO_DATA:
                raise ValueError("Desactiva SEED_DEMO_DATA en producción")
            if self.LLM_PROVIDER == "mock":
                raise ValueError("Producción requiere un proveedor de IA real")
            if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in {"", "/"} or url.hostname in {"localhost", "127.0.0.1", "::1"}:
                raise ValueError("Producción requiere PUBLIC_APP_URL con un origen HTTPS público")
            if not self.cors_origins or "*" in self.cors_origins or self.PUBLIC_APP_URL.rstrip('/') not in self.cors_origins:
                raise ValueError("Configura CORS_ORIGINS con el origen público explícito")
            if any(urlsplit(origin).scheme != "https" for origin in self.cors_origins):
                raise ValueError("Los orígenes de producción deben utilizar HTTPS")
            if "*" in self.allowed_hosts or url.hostname not in self.allowed_hosts:
                raise ValueError("Configura ALLOWED_HOSTS con el dominio público explícito")
        return self


settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.MATERIALS_DIR, exist_ok=True)
os.makedirs(settings.WORKS_DIR, exist_ok=True)
