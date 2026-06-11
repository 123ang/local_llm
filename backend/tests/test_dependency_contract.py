import unittest
from pathlib import Path


class DependencyContractTests(unittest.TestCase):
    def test_unused_langchain_stack_is_not_installed(self):
        requirements = (
            Path(__file__).resolve().parents[1] / "requirements.txt"
        ).read_text(encoding="utf-8").lower()
        self.assertNotIn("langchain", requirements)

    def test_uum_import_tools_require_an_external_dump_path(self):
        repo_root = Path(__file__).resolve().parents[2]
        for relative_path in (
            "investment/setup_companies_and_data.py",
            "investment/fix_uum_import.py",
        ):
            source = (repo_root / relative_path).read_text(encoding="utf-8")
            self.assertIn("UUM_SQL_DUMP_PATH", source, relative_path)
            self.assertNotIn(
                'Path(__file__).parent.parent / "uum_db.sql"',
                source,
                relative_path,
            )

    def test_sensitive_runtime_artifacts_are_not_kept_in_repo_paths(self):
        repo_root = Path(__file__).resolve().parents[2]

        self.assertEqual(list(repo_root.glob("*.sql")), [])
        self.assertFalse((repo_root / "backend/storage/uploads/companies").exists())
        self.assertTrue((repo_root / "docs/manuals/ANDAI_User_Manual.docx").is_file())
        self.assertTrue((repo_root / "docs/assets/branding/andai 01.png").is_file())


if __name__ == "__main__":
    unittest.main()
