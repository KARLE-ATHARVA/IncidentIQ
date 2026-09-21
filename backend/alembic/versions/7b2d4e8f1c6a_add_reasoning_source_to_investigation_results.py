"""add reasoning source to investigation results

Revision ID: 7b2d4e8f1c6a
Revises: 6ce4ec7bf826
Create Date: 2026-09-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7b2d4e8f1c6a"
down_revision: Union[str, Sequence[str], None] = "6ce4ec7bf826"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "investigation_results",
        sa.Column(
            "reasoning_source",
            sa.Text(),
            nullable=False,
            server_default="ai",
        ),
    )


def downgrade() -> None:
    op.drop_column("investigation_results", "reasoning_source")
