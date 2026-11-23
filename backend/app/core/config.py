from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "StenoVision Artery Analysis Engine"
    
    # Primary Database: PostgreSQL (with persistent local fallback)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "stenovision_db"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/stenovision_db"
    
    # Security & Tokens
    SECRET_KEY: str = "stenovision-secret-key-development-2026-secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FIRST_ADMIN_EMAIL: str | None = "admin@stenovision.com"
    FIRST_ADMIN_PASSWORD: str | None = "adminpassword123"
    
    # Medical Image Storage (Local Multi-Tier Storage)
    STORAGE_ROOT: str = "storage"
    MAX_UPLOAD_MB: int = 50

    model_config = SettingsConfigDict(env_file=(ENV_PATH, ".env"), extra="ignore")


settings = Settings()
