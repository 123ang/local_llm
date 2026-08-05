"""add SME Phase 1 document metadata

Revision ID: 9b32a2c2f0b8
Revises: 5ff358eadabf
Create Date: 2026-05-20 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b32a2c2f0b8"
down_revision: Union[str, Sequence[str], None] = "5ff358eadabf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("approval_status", sa.String(length=50), nullable=False, server_default="approved"))
    op.add_column("documents", sa.Column("document_type", sa.String(length=100), nullable=False, server_default="policy"))
    op.add_column("documents", sa.Column("source_url", sa.String(length=1000), nullable=True))
    op.add_column("document_chunks", sa.Column("section_title", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("document_chunks", "section_title")
    op.drop_column("documents", "source_url")
    op.drop_column("documents", "document_type")
    op.drop_column("documents", "approval_status")
