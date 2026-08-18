"""add domain metadata and generation batches"""
from alembic import op
import sqlalchemy as sa

revision = "0002_domain_metadata"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("data_sources", sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("data_sources", sa.Column("field_signature", sa.String(500), nullable=False, server_default=""))
    op.add_column("data_sources", sa.Column("data_sha256", sa.String(64)))
    op.add_column("data_sources", sa.Column("quality_summary", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("workflow_defs", sa.Column("applicable_field_signature", sa.String(500), nullable=False, server_default=""))
    op.add_column("workflow_defs", sa.Column("last_used_at", sa.DateTime()))
    op.add_column("task_records", sa.Column("notice_config", sa.Text()))
    op.add_column("task_records", sa.Column("batch_id", sa.String(64)))
    op.add_column("task_records", sa.Column("output_sha256", sa.String(64)))
    op.create_table(
        "generation_batches",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("workflow_defs.id"), nullable=False),
        sa.Column("notice_config", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table("generation_batches")
    op.drop_column("task_records", "output_sha256")
    op.drop_column("task_records", "batch_id")
    op.drop_column("task_records", "notice_config")
    op.drop_column("workflow_defs", "last_used_at")
    op.drop_column("workflow_defs", "applicable_field_signature")
    op.drop_column("data_sources", "quality_summary")
    op.drop_column("data_sources", "data_sha256")
    op.drop_column("data_sources", "field_signature")
    op.drop_column("data_sources", "row_count")
