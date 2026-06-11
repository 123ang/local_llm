import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.core.errors import correlation_id_from_request, public_error_detail


class PublicErrorTests(unittest.TestCase):
    def test_uses_safe_existing_correlation_id(self):
        request = SimpleNamespace(
            state=SimpleNamespace(correlation_id="0f8fad5b-d9cb-469f-a165-70867728950e")
        )
        self.assertEqual(
            correlation_id_from_request(request),
            "0f8fad5b-d9cb-469f-a165-70867728950e",
        )

    def test_generates_correlation_id_without_leaking_exception(self):
        request = SimpleNamespace(state=SimpleNamespace())
        with patch("app.core.errors.uuid.uuid4", return_value="safe-correlation-id"):
            detail = public_error_detail(
                request,
                "Unable to import the SQL file.",
                RuntimeError("password=secret; SELECT * FROM users"),
            )
        self.assertEqual(
            detail,
            {
                "message": "Unable to import the SQL file.",
                "correlation_id": "safe-correlation-id",
            },
        )
        self.assertNotIn("secret", str(detail))
        self.assertNotIn("SELECT", str(detail))


if __name__ == "__main__":
    unittest.main()
