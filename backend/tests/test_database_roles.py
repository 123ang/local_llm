import unittest
from pathlib import Path

from app.core.database_roles import (
    dataset_role_statements,
    quote_database_identifier,
)


class DatabaseRoleTests(unittest.TestCase):
    def test_quotes_only_safe_role_and_table_identifiers(self):
        self.assertEqual(
            quote_database_identifier("askai_text_reader"),
            '"askai_text_reader"',
        )
        self.assertEqual(
            quote_database_identifier("c12_finance_data"),
            '"c12_finance_data"',
        )
        with self.assertRaisesRegex(ValueError, "Unsafe PostgreSQL identifier"):
            quote_database_identifier('reader"; DROP TABLE users; --')

    def test_dataset_transaction_uses_importer_and_grants_only_reader_select(self):
        statements = dataset_role_statements(
            table_name="c12_finance_data",
            importer_role="askai_dataset_importer",
            reader_role="askai_text_reader",
        )
        self.assertEqual(
            statements,
            (
                'SET LOCAL ROLE "askai_dataset_importer"',
                'GRANT SELECT ON TABLE "c12_finance_data" TO "askai_text_reader"',
            ),
        )
        self.assertNotIn("users", " ".join(statements))
        self.assertNotIn("ALL TABLES", " ".join(statements))

    def test_role_provisioning_template_uses_least_privilege_roles(self):
        repo_root = Path(__file__).resolve().parents[2]
        template = (repo_root / "deploy/postgres_roles.sql.example").read_text(
            encoding="utf-8"
        )

        self.assertIn("CREATE ROLE askai_text_reader LOGIN", template)
        self.assertIn("CREATE ROLE askai_dataset_importer NOLOGIN", template)
        self.assertIn("GRANT askai_dataset_importer TO askai_app", template)
        self.assertIn("GRANT USAGE ON SCHEMA public TO askai_text_reader", template)
        self.assertIn(
            "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE",
            template,
        )
        self.assertIn(
            "GRANT USAGE, SELECT ON SEQUENCE",
            template,
        )
        self.assertNotIn("SUPERUSER", template)
        self.assertNotIn("GRANT ALL", template)


if __name__ == "__main__":
    unittest.main()
