import unittest

from app.llm.unified_query import (
    _extract_sql_table_refs,
    _is_safe_select_sql,
    _sanitize_generated_sql,
    _sql_uses_only_allowed_tables,
)


class SqlSafetyTests(unittest.TestCase):
    def test_allows_single_select_from_allowed_table(self):
        self.assertTrue(
            _sql_uses_only_allowed_tables(
                'SELECT "sector", jobs_per_rm1b FROM kedah_sector_jobs_per_rm1b LIMIT 10',
                {"kedah_sector_jobs_per_rm1b"},
            )
        )

    def test_rejects_comma_join_to_unallowed_table(self):
        self.assertFalse(
            _sql_uses_only_allowed_tables(
                "SELECT * FROM c1_data, users",
                {"c1_data"},
            )
        )

    def test_rejects_join_to_unallowed_table(self):
        self.assertFalse(
            _sql_uses_only_allowed_tables(
                "SELECT * FROM c1_data JOIN users ON users.id = c1_data.user_id",
                {"c1_data"},
            )
        )

    def test_rejects_multiple_statements(self):
        self.assertFalse(
            _sql_uses_only_allowed_tables(
                "SELECT * FROM c1_data; SELECT * FROM users",
                {"c1_data"},
            )
        )

    def test_rejects_cte_that_can_hide_cross_table_access(self):
        self.assertFalse(
            _sql_uses_only_allowed_tables(
                "WITH stolen AS (SELECT * FROM users) SELECT * FROM c1_data",
                {"c1_data"},
            )
        )

    def test_allows_cte_when_every_physical_table_is_allowed(self):
        self.assertTrue(
            _sql_uses_only_allowed_tables(
                "WITH ranked AS (SELECT * FROM c1_data) SELECT * FROM ranked",
                {"c1_data"},
            )
        )

    def test_extracts_tables_from_nested_subqueries_and_ctes(self):
        self.assertEqual(
            _extract_sql_table_refs(
                "WITH ranked AS (SELECT * FROM c1_data) "
                "SELECT * FROM ranked WHERE EXISTS (SELECT 1 FROM c1_more)"
            ),
            {"c1_data", "c1_more"},
        )

    def test_rejects_select_into_and_locking_clauses(self):
        self.assertFalse(_is_safe_select_sql("SELECT * INTO leaked FROM c1_data"))
        self.assertFalse(_is_safe_select_sql("SELECT * FROM c1_data FOR UPDATE"))

    def test_rejects_postgres_file_and_command_functions(self):
        self.assertFalse(_is_safe_select_sql("SELECT pg_read_file('/etc/passwd')"))
        self.assertFalse(_is_safe_select_sql("SELECT * FROM pg_ls_dir('/')"))

    def test_rejects_dml_and_ddl(self):
        self.assertFalse(_is_safe_select_sql("DELETE FROM c1_data"))
        self.assertFalse(_is_safe_select_sql("DROP TABLE c1_data"))

    def test_extracts_comma_join_references(self):
        self.assertEqual(
            _extract_sql_table_refs("SELECT * FROM c1_data, c1_more WHERE c1_data.id = c1_more.id"),
            {"c1_data", "c1_more"},
        )

    def test_sanitizes_code_fence_and_trailing_semicolon(self):
        self.assertEqual(
            _sanitize_generated_sql("```sql\nSELECT * FROM c1_data;\n```"),
            "SELECT * FROM c1_data",
        )


if __name__ == "__main__":
    unittest.main()
