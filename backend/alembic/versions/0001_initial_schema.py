"""initial schema

Revision ID: 4a7c9f2d1e3b
Revises:
Create Date: 2026-05-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "4a7c9f2d1e3b"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("color", sa.String(7), nullable=False, server_default="#3B82F6"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_routes_id", "routes", ["id"])

    op.create_table(
        "stops",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.Column("code", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stops_id", "stops", ["id"])
    op.create_index("ix_stops_name", "stops", ["name"])

    op.create_table(
        "route_stops",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("stop_id", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["stop_id"], ["stops.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("route_id", "stop_id", "order_index", name="uq_route_stop_order"),
    )
    op.create_index("ix_route_stops_route_id", "route_stops", ["route_id"])
    op.create_index("ix_route_stops_stop_id", "route_stops", ["stop_id"])

    op.create_table(
        "user_queries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_queries_id", "user_queries", ["id"])


def downgrade() -> None:
    op.drop_table("user_queries")
    op.drop_table("route_stops")
    op.drop_table("stops")
    op.drop_table("routes")
