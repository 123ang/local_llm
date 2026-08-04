"""add department rbac

Revision ID: 9f31c2d4e8a7
Revises: 5ff358eadabf
Create Date: 2026-07-01 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f31c2d4e8a7"
down_revision: Union[str, Sequence[str], None] = "5ff358eadabf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "slug", name="uq_departments_company_slug"),
    )
    op.create_index(op.f("ix_departments_id"), "departments", ["id"], unique=False)
    op.create_index(op.f("ix_departments_company_id"), "departments", ["company_id"], unique=False)
    op.create_index(op.f("ix_departments_slug"), "departments", ["slug"], unique=False)

    op.create_table(
        "user_department_access",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("granted_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "department_id", name="uq_user_department_access"),
    )
    op.create_index(op.f("ix_user_department_access_id"), "user_department_access", ["id"], unique=False)
    op.create_index(op.f("ix_user_department_access_user_id"), "user_department_access", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_department_access_department_id"), "user_department_access", ["department_id"], unique=False)

    for table in ("documents", "document_chunks", "faq_items", "datasets"):
        op.add_column(table, sa.Column("department_id", sa.Integer(), nullable=True))
        op.add_column(table, sa.Column("visibility", sa.String(length=50), nullable=False, server_default="department"))
        op.create_index(op.f(f"ix_{table}_department_id"), table, ["department_id"], unique=False)
        op.create_foreign_key(f"fk_{table}_department_id_departments", table, "departments", ["department_id"], ["id"])

    op.add_column("dataset_imports", sa.Column("department_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_dataset_imports_department_id"), "dataset_imports", ["department_id"], unique=False)
    op.create_foreign_key(
        "fk_dataset_imports_department_id_departments",
        "dataset_imports",
        "departments",
        ["department_id"],
        ["id"],
    )

    op.add_column("chat_sessions", sa.Column("department_ids", sa.JSON(), nullable=True))

    op.execute(
        """
        INSERT INTO departments (company_id, name, slug, description, is_active)
        SELECT c.id, 'General', 'general', 'Default department for existing knowledge', true
        FROM companies c
        WHERE NOT EXISTS (
            SELECT 1 FROM departments d WHERE d.company_id = c.id AND d.slug = 'general'
        )
        """
    )

    for table in ("documents", "document_chunks", "faq_items", "datasets", "dataset_imports"):
        op.execute(
            f"""
            UPDATE {table} target
            SET department_id = d.id
            FROM departments d
            WHERE target.company_id = d.company_id
              AND d.slug = 'general'
              AND target.department_id IS NULL
            """
        )

    op.execute(
        """
        INSERT INTO user_department_access (user_id, department_id, granted_by)
        SELECT u.id, d.id, NULL
        FROM users u
        JOIN departments d ON d.company_id = u.company_id AND d.slug = 'general'
        WHERE u.company_id IS NOT NULL
        ON CONFLICT ON CONSTRAINT uq_user_department_access DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_column("chat_sessions", "department_ids")

    op.drop_constraint("fk_dataset_imports_department_id_departments", "dataset_imports", type_="foreignkey")
    op.drop_index(op.f("ix_dataset_imports_department_id"), table_name="dataset_imports")
    op.drop_column("dataset_imports", "department_id")

    for table in ("datasets", "faq_items", "document_chunks", "documents"):
        op.drop_constraint(f"fk_{table}_department_id_departments", table, type_="foreignkey")
        op.drop_index(op.f(f"ix_{table}_department_id"), table_name=table)
        op.drop_column(table, "visibility")
        op.drop_column(table, "department_id")

    op.drop_index(op.f("ix_user_department_access_department_id"), table_name="user_department_access")
    op.drop_index(op.f("ix_user_department_access_user_id"), table_name="user_department_access")
    op.drop_index(op.f("ix_user_department_access_id"), table_name="user_department_access")
    op.drop_table("user_department_access")

    op.drop_index(op.f("ix_departments_slug"), table_name="departments")
    op.drop_index(op.f("ix_departments_company_id"), table_name="departments")
    op.drop_index(op.f("ix_departments_id"), table_name="departments")
    op.drop_table("departments")
