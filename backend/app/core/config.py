from pathlib import Path
import re
from urllib.parse import urlsplit

from pydantic_settings import BaseSettings

INSECURE_SECRET_KEYS = {
    "",
    "askai-dev-secret-change-in-production",
    "generate-a-strong-random-key-here",
    "change_me_64_random_chars",
}
INSECURE_SUPER_ADMIN_PASSWORDS = {"", "admin123", "password", "change_me"}
DATABASE_ROLE_RE = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
DATABASE_URL_PLACEHOLDERS = ("920214", "YOUR_PASSWORD", "REPLACE_ME")


class Settings(BaseSettings):
    PROJECT_NAME: str = "Adaptive Neural Decision AI"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://postgres@localhost:5432/askai"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres@localhost:5432/askai"
    TEXT_TO_SQL_DATABASE_URL: str = ""
    TEXT_TO_SQL_DB_ROLE: str = "askai_text_reader"
    DATASET_IMPORT_DB_ROLE: str = "askai_dataset_importer"

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "gemma4:latest"
    LLM_MODEL_FAST: str = "qwen2.5-coder:1.5b"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    CHROMA_PERSIST_DIR: str = "./storage/chromadb"
    UPLOAD_DIR: str = "./storage/uploads"
    MAX_SQL_UPLOAD_BYTES: int = 10 * 1024 * 1024
    MAX_SQL_IMPORT_TABLES: int = 25
    MAX_SQL_IMPORT_COLUMNS_PER_TABLE: int = 200
    MAX_SQL_IMPORT_ROWS: int = 100_000

    FRONTEND_URL: str = "http://localhost:3000"
    # Comma-separated extra allowed CORS origins (e.g. https://www.andai.my)
    CORS_EXTRA_ORIGINS: str = ""
    TRUST_PROXY_HEADERS: bool = False

    SUPER_ADMIN_EMAIL: str = "admin@askai.local"
    SUPER_ADMIN_PASSWORD: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


def validate_runtime_security_settings(cfg: Settings = settings) -> None:
    if cfg.SECRET_KEY in INSECURE_SECRET_KEYS or len(cfg.SECRET_KEY) < 32:
        raise RuntimeError("Set SECRET_KEY to a strong random value before starting the backend")
    if (
        cfg.SUPER_ADMIN_PASSWORD in INSECURE_SUPER_ADMIN_PASSWORDS
        or len(cfg.SUPER_ADMIN_PASSWORD) < 12
    ):
        raise RuntimeError("Set SUPER_ADMIN_PASSWORD to a strong initial password before starting the backend")
    for value_name in ("DATABASE_URL", "DATABASE_URL_SYNC", "TEXT_TO_SQL_DATABASE_URL"):
        value = getattr(cfg, value_name)
        normalized_value = (value or "").upper()
        if not value or any(
            placeholder in normalized_value
            for placeholder in DATABASE_URL_PLACEHOLDERS
        ):
            raise RuntimeError(f"Remove placeholder or exposed credentials from {value_name}")

    for role_name in ("TEXT_TO_SQL_DB_ROLE", "DATASET_IMPORT_DB_ROLE"):
        role = getattr(cfg, role_name)
        if not DATABASE_ROLE_RE.fullmatch(role):
            raise RuntimeError(f"{role_name} must be a simple PostgreSQL role identifier")

    app_username = urlsplit(cfg.DATABASE_URL).username
    reader_username = urlsplit(cfg.TEXT_TO_SQL_DATABASE_URL).username
    if not reader_username or reader_username != cfg.TEXT_TO_SQL_DB_ROLE:
        raise RuntimeError(
            "TEXT_TO_SQL_DATABASE_URL must authenticate as TEXT_TO_SQL_DB_ROLE"
        )
    if reader_username == app_username:
        raise RuntimeError(
            "TEXT_TO_SQL_DATABASE_URL must use a dedicated role, not the application role"
        )
    if cfg.DATASET_IMPORT_DB_ROLE in {app_username, cfg.TEXT_TO_SQL_DB_ROLE}:
        raise RuntimeError(
            "DATASET_IMPORT_DB_ROLE must be distinct from the application and text-to-SQL roles"
        )


def build_cors_origins(cfg: Settings = settings) -> list[str]:
    origins = [cfg.FRONTEND_URL]
    if cfg.ENVIRONMENT.lower() != "production":
        origins.extend(["http://localhost:3000", "http://localhost:3001"])
    if cfg.CORS_EXTRA_ORIGINS:
        origins.extend(o.strip() for o in cfg.CORS_EXTRA_ORIGINS.split(",") if o.strip())

    seen = set()
    unique_origins = []
    for origin in origins:
        if origin and origin not in seen:
            seen.add(origin)
            unique_origins.append(origin)
    return unique_origins

UPLOAD_PATH = Path(settings.UPLOAD_DIR)
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
