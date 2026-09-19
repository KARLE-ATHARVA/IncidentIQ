"""add alternative explanations to investigation results

Revision ID: 01f8fb8595a9
Revises: 9fe2411f05aa
Create Date: 2026-09-18 22:57:58.247819

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "01f8fb8595a9"

down_revision: Union[str, Sequence[str], None] = "9fe2411f05aa"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "investigation_results",
        sa.Column(
            "alternative_explanations",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "investigation_results",
        "alternative_explanations",
    )