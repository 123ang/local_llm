"""add api connectors

Revision ID: a82b6f5d13c0
Revises: 9f31c2d4e8a7
Create Date: 2026-07-01 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a82b6f5d13c0"
down_revision: Union[str, Sequence[str], None] = "9f31c2d4e8a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_connectors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("visibility", sa.String(length=50), nullable=False, server_default="department"),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("method", sa.String(length=20), nullable=False, server_default="GET"),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("headers", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("curl_command", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("last_response_text", sa.Text(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_connectors_id"), "api_connectors", ["id"], unique=False)
    op.create_index(op.f("ix_api_connectors_company_id"), "api_connectors", ["company_id"], unique=False)
    op.create_index(op.f("ix_api_connectors_department_id"), "api_connectors", ["department_id"], unique=False)
    op.execute(
        """
        UPDATE company_ai_settings
        SET allowed_sources = (COALESCE(allowed_sources::jsonb, '[]'::jsonb) || '["apis"]'::jsonb)::json
        WHERE NOT (COALESCE(allowed_sources::jsonb, '[]'::jsonb) ? 'apis')
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE company_ai_settings
        SET allowed_sources = COALESCE(
            (
                SELECT json_agg(value)
                FROM json_array_elements_text(allowed_sources) AS value
                WHERE value <> 'apis'
            ),
            '[]'::json
        )
        """
    )
    op.drop_index(op.f("ix_api_connectors_department_id"), table_name="api_connectors")
    op.drop_index(op.f("ix_api_connectors_company_id"), table_name="api_connectors")
    op.drop_index(op.f("ix_api_connectors_id"), table_name="api_connectors")
    op.drop_table("api_connectors")
