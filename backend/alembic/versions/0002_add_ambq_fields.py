"""add ambq fields to routes

Revision ID: 7b2e4f8c1a9d
Revises: 4a7c9f2d1e3b
Create Date: 2026-05-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "7b2e4f8c1a9d"
down_revision: Union[str, None] = "4a7c9f2d1e3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("routes", sa.Column("empresa", sa.String(100), nullable=True))
    op.add_column("routes", sa.Column("recorrido", sa.Text(), nullable=True))
    op.add_column("routes", sa.Column("calles", postgresql.JSONB(), nullable=True))
    op.add_column("routes", sa.Column("fuente", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("routes", "fuente")
    op.drop_column("routes", "calles")
    op.drop_column("routes", "recorrido")
    op.drop_column("routes", "empresa")
