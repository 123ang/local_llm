import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from app.core.dependencies import filter_requested_department_ids, get_user_department_ids, role_can_curate_knowledge
from app.models.department import Department, UserDepartmentAccess


class _RowsResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeAsyncSession:
    def __init__(self, results):
        self._results = list(results)
        self.added = []
        self.commits = 0

    async def execute(self, _statement):
        return self._results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        for obj in self.added:
            if isinstance(obj, Department) and obj.id is None:
                obj.id = 9

    async def commit(self):
        self.commits += 1


class DepartmentRbacContractTests(unittest.TestCase):
    def test_department_scope_defaults_to_user_grants(self):
        user = SimpleNamespace(role="user")

        self.assertEqual(
            filter_requested_department_ids(user, requested_department_ids=None, granted_department_ids=[3, 1, 3]),
            [1, 3],
        )

    def test_department_scope_rejects_ungranted_department(self):
        user = SimpleNamespace(role="user")

        with self.assertRaises(HTTPException) as exc:
            filter_requested_department_ids(user, requested_department_ids=[7], granted_department_ids=[3])

        self.assertEqual(exc.exception.status_code, 403)

    def test_only_department_admin_curates_knowledge(self):
        self.assertTrue(role_can_curate_knowledge(SimpleNamespace(role="admin")))
        self.assertFalse(role_can_curate_knowledge(SimpleNamespace(role="super_admin")))
        self.assertFalse(role_can_curate_knowledge(SimpleNamespace(role="user")))


class DepartmentDefaultAccessTests(unittest.IsolatedAsyncioTestCase):
    async def test_admin_without_department_gets_existing_general_access(self):
        general = Department(id=8, company_id=4, name="General", slug="general", is_active=True)
        db = _FakeAsyncSession([_RowsResult([]), _ScalarResult(general)])

        department_ids = await get_user_department_ids(
            db,
            SimpleNamespace(id=12, role="admin", company_id=4),
            company_id=4,
        )

        self.assertEqual(department_ids, [8])
        grants = [obj for obj in db.added if isinstance(obj, UserDepartmentAccess)]
        self.assertEqual(len(grants), 1)
        self.assertEqual(grants[0].user_id, 12)
        self.assertEqual(grants[0].department_id, 8)
        self.assertEqual(db.commits, 1)

    async def test_regular_user_without_department_stays_unassigned(self):
        db = _FakeAsyncSession([_RowsResult([])])

        department_ids = await get_user_department_ids(
            db,
            SimpleNamespace(id=13, role="user", company_id=4),
            company_id=4,
        )

        self.assertEqual(department_ids, [])
        self.assertEqual(db.added, [])

    async def test_admin_without_general_department_gets_new_general_access(self):
        db = _FakeAsyncSession([_RowsResult([]), _ScalarResult(None)])

        department_ids = await get_user_department_ids(
            db,
            SimpleNamespace(id=14, role="admin", company_id=5),
            company_id=5,
        )

        self.assertEqual(department_ids, [9])
        departments = [obj for obj in db.added if isinstance(obj, Department)]
        grants = [obj for obj in db.added if isinstance(obj, UserDepartmentAccess)]
        self.assertEqual(len(departments), 1)
        self.assertEqual(departments[0].name, "General")
        self.assertEqual(departments[0].slug, "general")
        self.assertEqual(grants[0].user_id, 14)
        self.assertEqual(grants[0].department_id, 9)


if __name__ == "__main__":
    unittest.main()
