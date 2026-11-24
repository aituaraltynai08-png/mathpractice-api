"""add password hash to users

Revision ID: 0003_password_hash
Revises: d54937a5299a
Create Date: 2026-11-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_password_hash"
down_revision: Union[str, Sequence[str], None] = "d54937a5299a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users that already exist get an empty hash (they can't log in until they register again
    # or the demo data is recreated); new users always get a real bcrypt hash
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=False, server_default=""))
    op.alter_column("users", "password_hash", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "password_hash")
