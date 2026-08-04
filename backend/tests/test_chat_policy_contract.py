import unittest

from app.api.chat import _resolve_ai_insights


class ChatPolicyContractTests(unittest.TestCase):
    def test_requested_ai_insights_remain_enabled_without_department_scope(self):
        self.assertTrue(
            _resolve_ai_insights(
                requested_ai_insights=True,
                default_source_only=True,
                ai_insights_allowed=True,
            )
        )

    def test_company_source_only_default_still_applies_when_unrequested(self):
        self.assertFalse(
            _resolve_ai_insights(
                requested_ai_insights=None,
                default_source_only=True,
                ai_insights_allowed=True,
            )
        )

    def test_company_can_disable_ai_insights(self):
        self.assertFalse(
            _resolve_ai_insights(
                requested_ai_insights=True,
                default_source_only=False,
                ai_insights_allowed=False,
            )
        )


if __name__ == "__main__":
    unittest.main()
