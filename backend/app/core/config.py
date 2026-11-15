import os
from pathlib import Path
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseModel as BaseSettings
    SettingsConfigDict = None

# Check potential .env locations in root and env/ folder
_ENV_LOCATIONS = [
    Path(".env"),
    Path("../env/.env.development"),
    Path("../env/.env.production"),
    Path("env/.env.development"),
    Path("env/.env.production"),
]
_active_env_file = next((str(p) for p in _ENV_LOCATIONS if p.exists()), ".env")


class Settings(BaseSettings):
    if SettingsConfigDict:
        model_config = SettingsConfigDict(env_file=_active_env_file, extra="ignore")
    else:
        class Config:
            env_file = _active_env_file
            extra = "ignore"

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./enterprise_helpdesk.db")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
