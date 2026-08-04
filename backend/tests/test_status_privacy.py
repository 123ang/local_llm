import inspect
import unittest

from app.api import status


class StatusPrivacyTests(unittest.TestCase):
    def test_status_endpoint_does_not_expose_model_inventory(self):
        source = inspect.getsource(status.get_status)
        self.assertNotIn("ollama_models", source)
        self.assertNotIn('"models"', source)
        self.assertNotIn("OLLAMA_BASE_URL", source.split("return", 1)[-1])


if __name__ == "__main__":
    unittest.main()
