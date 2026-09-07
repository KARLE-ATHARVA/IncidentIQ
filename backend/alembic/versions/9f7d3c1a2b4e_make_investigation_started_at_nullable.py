"""make investigation started_at nullable

Revision ID: 9f7d3c1a2b4e
Revises: a7c99557b264
Create Date: 2026-09-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "9f7d3c1a2b4e"
down_revision: Union[str, Sequence[str], None] = "a7c99557b264"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "investigations",
        "started_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "investigations",
        "started_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
