import unittest

from app.api.users import _department_ids_or_default


class _DepartmentRows:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeAsyncSession:
    async def execute(self, _statement):
        return _DepartmentRows([(8,)])


class UserDepartmentDefaultTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_department_ids_default_to_general_department(self):
        department_ids = await _department_ids_or_default(
            _FakeAsyncSession(),
            company_id=3,
            requested_department_ids=[],
        )

        self.assertEqual(department_ids, [8])

    async def test_explicit_department_ids_are_preserved(self):
        department_ids = await _department_ids_or_default(
            _FakeAsyncSession(),
            company_id=3,
            requested_department_ids=[4, 2],
        )

        self.assertEqual(department_ids, [4, 2])


if __name__ == "__main__":
    unittest.main()
