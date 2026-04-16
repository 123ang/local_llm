from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_NAME: str = "Adaptive Neural Decision AI"
    API_PREFIX: str = "/api"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:920214@localhost:5432/askai"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:920214@localhost:5432/askai"

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "askai-dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "gemma4:latest"
    LLM_MODEL_FAST: str = "qwen2.5-coder:1.5b"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    CHROMA_PERSIST_DIR: str = "./storage/chromadb"
    UPLOAD_DIR: str = "./storage/uploads"

    FRONTEND_URL: str = "http://localhost:3000"
    # Comma-separated extra allowed CORS origins (e.g. https://www.andai.my)
    CORS_EXTRA_ORIGINS: str = ""

    SUPER_ADMIN_EMAIL: str = "admin@askai.local"
    SUPER_ADMIN_PASSWORD: str = "admin123"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

UPLOAD_PATH = Path(settings.UPLOAD_DIR)
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
