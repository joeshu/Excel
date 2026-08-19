"""add workflow mapping and workbook profile tables"""
from alembic import op
import sqlalchemy as sa


revision = "0004_workflow_mapping_profiles"
down_revision = "0003_users_and_batch_package"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("task_records", sa.Column("mapping_snapshot_id", sa.Integer(), nullable=True))
    op.create_table(
        "template_workbook_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile", sa.JSON(), nullable=False),
        sa.Column("validation_result", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("template_id", name="uq_template_workbook_profile_template"),
    )
    op.create_table(
        "mapping_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("workflow_defs.id"), nullable=False),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("templates.id"), nullable=False),
        sa.Column("template_version", sa.String(30), nullable=False),
        sa.Column("data_field_signature", sa.String(500), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("dependency_order", sa.JSON(), nullable=False),
        sa.Column("validation_result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "mapping_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("workflow_defs.id"), nullable=False),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("templates.id"), nullable=False),
        sa.Column("data_source_id", sa.Integer(), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("template_version", sa.String(30), nullable=False),
        sa.Column("data_field_signature", sa.String(500), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("dependency_order", sa.JSON(), nullable=False),
        sa.Column("validation_result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("task_records", "mapping_snapshot_id")
    op.drop_table("mapping_snapshots")
    op.drop_table("mapping_rules")
    op.drop_table("template_workbook_profiles")
