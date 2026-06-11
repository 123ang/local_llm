import unittest
from pathlib import Path
from types import SimpleNamespace

from app.core.config import build_cors_origins, settings, validate_runtime_security_settings


class ConfigSecurityTests(unittest.TestCase):
    @staticmethod
    def secure_config(**overrides):
        values = {
            "SECRET_KEY": "x" * 40,
            "SUPER_ADMIN_PASSWORD": "StrongEnough123!",
            "DATABASE_URL": "postgresql+asyncpg://askai_app@localhost:5432/askai",
            "DATABASE_URL_SYNC": "postgresql+psycopg2://askai_app@localhost:5432/askai",
            "TEXT_TO_SQL_DATABASE_URL": "postgresql+asyncpg://askai_text_reader@localhost:5432/askai",
            "TEXT_TO_SQL_DB_ROLE": "askai_text_reader",
            "DATASET_IMPORT_DB_ROLE": "askai_dataset_importer",
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_default_database_urls_do_not_contain_exposed_password(self):
        self.assertNotIn("920214", settings.DATABASE_URL)
        self.assertNotIn("920214", settings.DATABASE_URL_SYNC)

    def test_repository_docs_and_configs_do_not_contain_exposed_defaults(self):
        repo_root = Path(__file__).resolve().parents[2]
        for relative_path in ("README.md", "backend/alembic.ini", ".env.example"):
            source = (repo_root / relative_path).read_text(encoding="utf-8")
            self.assertNotIn("920214", source, relative_path)
            self.assertNotIn("admin123", source, relative_path)

    def test_rejects_insecure_secret_key(self):
        cfg = self.secure_config(
            SECRET_KEY="askai-dev-secret-change-in-production",
        )
        with self.assertRaisesRegex(RuntimeError, "SECRET_KEY"):
            validate_runtime_security_settings(cfg)

    def test_rejects_default_super_admin_password(self):
        cfg = self.secure_config(
            SUPER_ADMIN_PASSWORD="admin123",
        )
        with self.assertRaisesRegex(RuntimeError, "SUPER_ADMIN_PASSWORD"):
            validate_runtime_security_settings(cfg)

    def test_rejects_database_url_placeholders_from_example_env(self):
        cfg = self.secure_config(
            DATABASE_URL=(
                "postgresql+asyncpg://askai_app:REPLACE_ME@localhost:5432/askai"
            ),
        )
        with self.assertRaisesRegex(RuntimeError, "DATABASE_URL"):
            validate_runtime_security_settings(cfg)

    def test_accepts_strong_runtime_values(self):
        cfg = self.secure_config()
        validate_runtime_security_settings(cfg)

    def test_requires_dedicated_text_to_sql_database_role(self):
        cfg = self.secure_config(
            TEXT_TO_SQL_DATABASE_URL="postgresql+asyncpg://askai_app@localhost:5432/askai",
        )
        with self.assertRaisesRegex(RuntimeError, "TEXT_TO_SQL_DATABASE_URL"):
            validate_runtime_security_settings(cfg)

    def test_rejects_unsafe_database_role_identifiers(self):
        cfg = self.secure_config(TEXT_TO_SQL_DB_ROLE='reader"; DROP ROLE askai_app; --')
        with self.assertRaisesRegex(RuntimeError, "TEXT_TO_SQL_DB_ROLE"):
            validate_runtime_security_settings(cfg)

    def test_production_cors_does_not_add_localhost_defaults(self):
        cfg = SimpleNamespace(
            FRONTEND_URL="https://andai.example.com",
            CORS_EXTRA_ORIGINS="https://admin.example.com",
            ENVIRONMENT="production",
        )
        self.assertEqual(
            build_cors_origins(cfg),
            ["https://andai.example.com", "https://admin.example.com"],
        )

    def test_development_cors_keeps_localhost_defaults(self):
        cfg = SimpleNamespace(
            FRONTEND_URL="http://localhost:3000",
            CORS_EXTRA_ORIGINS="",
            ENVIRONMENT="development",
        )
        self.assertEqual(
            build_cors_origins(cfg),
            ["http://localhost:3000", "http://localhost:3001"],
        )


if __name__ == "__main__":
    unittest.main()
