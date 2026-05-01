"""partial active status index

Revision ID: 22e2061c70e8
Revises: a2e3d26ff009
Create Date: 2026-05-01 08:15:23.875437

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22e2061c70e8'
down_revision: Union[str, Sequence[str], None] = 'a2e3d26ff009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index("idx_stores_active_status", table_name="stores")
    op.create_index(
        "idx_stores_active_status",
        "stores",
        ["status"],
        unique=False,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_stores_active_status", table_name="stores")
    op.create_index("idx_stores_active_status", "stores", ["status"], unique=False)
