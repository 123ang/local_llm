import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.audit_service import serialize_audit_log


class AuditLogDisplayTests(unittest.TestCase):
    def test_serialized_log_includes_user_organization_and_resource_labels(self):
        entry = SimpleNamespace(
            id=7,
            company_id=4,
            user_id=22,
            action="create_user",
            resource_type="user",
            resource_id=23,
            details=None,
            ip_address="127.0.0.1",
            created_at=datetime(2026, 7, 12, tzinfo=timezone.utc),
        )
        users = {
            22: SimpleNamespace(full_name="Airport Admin", email="airportadmin@andai.my"),
        }
        companies = {
            4: SimpleNamespace(name="Airport"),
        }
        resource_labels = {
            ("user", 23): "Airport Staff (staff@andai.my)",
        }

        result = serialize_audit_log(entry, users=users, companies=companies, resource_labels=resource_labels)

        self.assertEqual(result["user_name"], "Airport Admin")
        self.assertEqual(result["user_email"], "airportadmin@andai.my")
        self.assertEqual(result["actor_label"], "Airport Admin (airportadmin@andai.my)")
        self.assertEqual(result["organization_name"], "Airport")
        self.assertEqual(result["company_name"], "Airport")
        self.assertEqual(result["resource_kind_label"], "User")
        self.assertEqual(result["resource_label"], "Airport Staff (staff@andai.my)")

    def test_missing_resource_uses_clear_unavailable_label_not_hash_id(self):
        entry = SimpleNamespace(
            id=8,
            company_id=None,
            user_id=None,
            action="delete_user",
            resource_type="user",
            resource_id=22,
            details=None,
            ip_address=None,
            created_at=datetime(2026, 7, 12, tzinfo=timezone.utc),
        )

        result = serialize_audit_log(entry, users={}, companies={}, resource_labels={})

        self.assertEqual(result["actor_label"], "System")
        self.assertIsNone(result["organization_name"])
        self.assertEqual(result["resource_label"], "Unavailable user (ID 22)")

    def test_company_resource_can_fill_organization_label(self):
        entry = SimpleNamespace(
            id=9,
            company_id=None,
            user_id=22,
            action="create_company",
            resource_type="company",
            resource_id=4,
            details=None,
            ip_address=None,
            created_at=datetime(2026, 7, 12, tzinfo=timezone.utc),
        )
        users = {
            22: SimpleNamespace(full_name="Super Admin", email="admin@andai.my"),
        }
        companies = {
            4: SimpleNamespace(name="Airport"),
        }

        result = serialize_audit_log(entry, users=users, companies=companies, resource_labels={("company", 4): "Airport"})

        self.assertEqual(result["organization_name"], "Airport")
        self.assertEqual(result["resource_label"], "Airport")


if __name__ == "__main__":
    unittest.main()
