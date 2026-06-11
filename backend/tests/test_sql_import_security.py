import unittest

from app.ingestion.sql_importer import (
    SQLImportLimits,
    SQLImportValidationError,
    parse_sql_dump,
    read_sql_upload,
)


CREATE_ONE_ROW = """
CREATE TABLE `people` (
  `id` int NOT NULL,
  `name` varchar(100)
);
INSERT INTO `people` (`id`, `name`) VALUES (1, 'Alice');
"""


class SqlImportSecurityTests(unittest.TestCase):
    def test_rejects_unknown_column_types(self):
        sql = "CREATE TABLE `events` (`payload` made_up_type);"
        with self.assertRaisesRegex(SQLImportValidationError, "Unsupported SQL column type"):
            parse_sql_dump(sql)

    def test_rejects_too_many_tables(self):
        sql = (
            "CREATE TABLE `one` (`id` int);"
            "CREATE TABLE `two` (`id` int);"
        )
        with self.assertRaisesRegex(SQLImportValidationError, "table limit"):
            parse_sql_dump(sql, limits=SQLImportLimits(max_tables=1))

    def test_rejects_too_many_columns(self):
        sql = "CREATE TABLE `wide` (`a` int, `b` int);"
        with self.assertRaisesRegex(SQLImportValidationError, "column limit"):
            parse_sql_dump(sql, limits=SQLImportLimits(max_columns_per_table=1))

    def test_rejects_too_many_rows(self):
        sql = """
        CREATE TABLE `people` (`id` int, `name` varchar(100));
        INSERT INTO `people` (`id`, `name`) VALUES (1, 'Alice'), (2, 'Bob');
        """
        with self.assertRaisesRegex(SQLImportValidationError, "row limit"):
            parse_sql_dump(sql, limits=SQLImportLimits(max_total_rows=1))

    def test_valid_dump_remains_supported(self):
        tables = parse_sql_dump(
            CREATE_ONE_ROW,
            limits=SQLImportLimits(
                max_tables=2,
                max_columns_per_table=10,
                max_total_rows=10,
            ),
        )
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0].row_count, 1)
        self.assertEqual([column.pg_type for column in tables[0].columns], ["INTEGER", "VARCHAR(100)"])


class SqlUploadLimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_upload_before_reading_past_hard_cap(self):
        class FakeUpload:
            def __init__(self):
                self.requested_size = None

            async def read(self, size):
                self.requested_size = size
                return b"x" * size

        upload = FakeUpload()
        with self.assertRaisesRegex(SQLImportValidationError, "size limit"):
            await read_sql_upload(upload, max_bytes=10)
        self.assertEqual(upload.requested_size, 11)


if __name__ == "__main__":
    unittest.main()
