import unittest

from app.models.company import Company
from app.models.department import Department
from app.services.company_service import create_company


class _EmptyResult:
    def scalar_one_or_none(self):
        return None


class _FakeAsyncSession:
    def __init__(self):
        self.added = []
        self.commits = 0
        self._next_company_id = 100

    async def execute(self, _statement):
        return _EmptyResult()

    def add(self, obj):
        if isinstance(obj, Company) and obj.id is None:
            obj.id = self._next_company_id
            self._next_company_id += 1
        self.added.append(obj)

    async def flush(self):
        for obj in self.added:
            if isinstance(obj, Company) and obj.id is None:
                obj.id = self._next_company_id
                self._next_company_id += 1

    async def commit(self):
        self.commits += 1

    async def refresh(self, obj):
        if isinstance(obj, Company) and obj.id is None:
            obj.id = self._next_company_id
            self._next_company_id += 1


class CompanyServiceContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_company_creates_default_general_department(self):
        db = _FakeAsyncSession()

        company = await create_company(db, name="Credit")

        departments = [obj for obj in db.added if isinstance(obj, Department)]
        self.assertEqual(len(departments), 1)
        self.assertEqual(departments[0].company_id, company.id)
        self.assertEqual(departments[0].name, "General")
        self.assertEqual(departments[0].slug, "general")
        self.assertTrue(departments[0].is_active)


if __name__ == "__main__":
    unittest.main()
