import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "IntegriEval"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
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
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "integrieval@gmail.com"
    SMTP_ENABLED: bool = False
    
    # LLM Settings (RI-001, RF-014, RNF-007)
    LLM_PROVIDER: str = "mock"  # mock, ollama, openai, anthropic
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "http://localhost:11434"  # Default for Ollama
    LLM_MODEL: str = "llama3.2"
    LLM_TIMEOUT_SECONDS: float = 30.0  # RNF-007: Fallback si timeout > 30s
    
    # Host and Port
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.MATERIALS_DIR, exist_ok=True)
os.makedirs(settings.WORKS_DIR, exist_ok=True)
