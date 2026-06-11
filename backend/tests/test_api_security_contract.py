import inspect
import unittest

from app.api import chat, datasets
from app.ingestion import pdf_processor


class ApiSecurityContractTests(unittest.TestCase):
    def test_sql_upload_routes_use_bounded_reader_and_restricted_role(self):
        source = inspect.getsource(datasets)
        self.assertIn("read_sql_upload", source)
        self.assertIn("dataset_write_transaction", source)
        self.assertNotIn("raw_bytes = await file.read()", source)
        self.assertNotIn("raw = (await file.read())", source)

    def test_api_exception_paths_do_not_serialize_raw_exception_text(self):
        chat_source = inspect.getsource(chat.ask_question)
        datasets_source = inspect.getsource(datasets.upload_sql)
        self.assertNotIn("str(e)", chat_source)
        self.assertNotIn("str(e)", datasets_source)
        self.assertIn("public_error_detail", chat_source)
        self.assertIn("public_error_detail", datasets_source)

    def test_document_failures_store_reference_not_exception_text(self):
        source = inspect.getsource(pdf_processor._run_pipeline)
        self.assertNotIn("doc.error_message = str(e)", source)
        self.assertIn("correlation_id", source)


if __name__ == "__main__":
    unittest.main()
