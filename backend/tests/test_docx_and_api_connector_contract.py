import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from app.ingestion.office_parser import extract_text_from_docx
from app.services.api_connector_service import parse_curl_command


class DocxAndApiConnectorContractTests(unittest.TestCase):
    def test_extracts_paragraph_text_from_docx(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "policy.docx"
            document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Leave policy</w:t></w:r></w:p>
    <w:p><w:r><w:t>Annual leave requires approval.</w:t></w:r></w:p>
  </w:body>
</w:document>"""
            with zipfile.ZipFile(path, "w") as docx:
                docx.writestr("word/document.xml", document_xml)

            pages = extract_text_from_docx(path)

        self.assertEqual(
            pages,
            [{"page": 1, "text": "Leave policy\nAnnual leave requires approval."}],
        )

    def test_parse_curl_command_supports_post_headers_and_json_body_without_shell(self):
        parsed = parse_curl_command(
            "curl -X POST https://example.com/api/policy "
            "-H 'Authorization: Bearer demo' "
            "-H 'Content-Type: application/json' "
            "-d '{\"department\":\"HR\"}'"
        )

        self.assertEqual(parsed.method, "POST")
        self.assertEqual(parsed.url, "https://example.com/api/policy")
        self.assertEqual(parsed.headers["Authorization"], "Bearer demo")
        self.assertEqual(json.loads(parsed.body or "{}"), {"department": "HR"})


if __name__ == "__main__":
    unittest.main()
