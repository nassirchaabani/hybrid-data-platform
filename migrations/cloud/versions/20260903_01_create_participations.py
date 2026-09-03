"""Création de la table cloud des participations."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260903_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "participations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("member_ref", sa.Uuid(), nullable=False),
        sa.Column("program", sa.String(length=120), nullable=False),
        sa.Column("hours", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_participations_member_ref",
        "participations",
        ["member_ref"],
        unique=False,
    )
    op.create_index(
        "ix_participations_program",
        "participations",
        ["program"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_participations_program", table_name="participations")
    op.drop_index("ix_participations_member_ref", table_name="participations")
    op.drop_table("participations")
