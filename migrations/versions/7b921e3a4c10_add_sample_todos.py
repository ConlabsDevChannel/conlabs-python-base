"""Add public Todo sample table."""
from alembic import op
import sqlalchemy as sa

revision = "7b921e3a4c10"
down_revision = "2d1b09739f06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sample_todos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("sample_todos")
