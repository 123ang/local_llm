import unittest

from app.ingestion.section_titles import extract_section_title
from app.services.chat_audit import build_chat_audit_details
from app.services.source_policy import (
    DEFAULT_SOURCES,
    normalize_allowed_sources,
    source_only_refusal,
)


class SMEPhase1PolicyTests(unittest.TestCase):
    def test_source_policy_allows_only_documents_and_faq(self):
        self.assertEqual(DEFAULT_SOURCES, ["documents", "faq"])
        self.assertEqual(
            normalize_allowed_sources(["database", "documents", "faq"], ["database", "documents", "faq"]),
            ["documents", "faq"],
        )
        self.assertEqual(normalize_allowed_sources(["database"], ["database", "documents"]), [])

    def test_source_policy_defaults_to_phase1_sources(self):
        self.assertEqual(normalize_allowed_sources(None, None), ["documents", "faq"])
        self.assertEqual(normalize_allowed_sources(None, ["database", "documents"]), ["documents"])

    def test_source_only_refusal_is_techpedia_specific(self):
        message = source_only_refusal({"documents", "faq"})
        self.assertIn("Techpedia AI Assistant", message)
        self.assertIn("approved policy documents", message)
        self.assertNotIn("database", message.lower())
        self.assertNotIn("AI Insights", message)

    def test_section_title_detection(self):
        content = "2.1 Credit Assessment Policy\nAll facilities must follow the approved workflow."
        self.assertEqual(extract_section_title(content), "2.1 Credit Assessment Policy")

    def test_chat_audit_payload_keeps_required_fields(self):
        payload = build_chat_audit_details(
            session_id=12,
            question="What is the eligibility rule?",
            answer="Refer to section 2.1.",
            sources={"documents": [{"source": "Policy.pdf", "section": "2.1 Eligibility"}], "faq": []},
            response_time_ms=345,
            model_tier="instant",
        )
        self.assertEqual(payload["session_id"], 12)
        self.assertEqual(payload["question"], "What is the eligibility rule?")
        self.assertEqual(payload["sources"]["documents"][0]["section"], "2.1 Eligibility")
        self.assertEqual(payload["response_time_ms"], 345)
        self.assertFalse(payload["used_general_knowledge"])


if __name__ == "__main__":
    unittest.main()
