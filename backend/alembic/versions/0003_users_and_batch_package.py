"""add local users and batch output package support"""
from alembic import op
import sqlalchemy as sa

revision = "0003_users_and_batch_package"
down_revision = "0002_domain_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("local_users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(100), nullable=False, unique=True), sa.Column("role", sa.String(30), nullable=False, server_default="operator"), sa.Column("created_at", sa.DateTime(), nullable=False))


def downgrade() -> None:
    op.drop_table("local_users")
