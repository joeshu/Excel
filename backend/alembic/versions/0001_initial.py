"""create initial workflow platform tables"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("templates", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("file_path", sa.String(500), nullable=False), sa.Column("has_formula", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("column_meta", sa.JSON(), nullable=False), sa.Column("sheet_count", sa.Integer(), nullable=False, server_default="1"), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("created_by", sa.String(100)))
    op.create_table("workflow_defs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("template_id", sa.Integer(), sa.ForeignKey("templates.id"), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("mode", sa.String(20), nullable=False), sa.Column("node_json", sa.JSON(), nullable=False), sa.Column("column_mapping", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("data_sources", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("source_type", sa.String(20), nullable=False), sa.Column("schema", sa.JSON(), nullable=False), sa.Column("file_path", sa.String(500)), sa.Column("connection_info", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("workflow_nodes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("workflow_defs.id", ondelete="CASCADE"), nullable=False), sa.Column("node_type", sa.String(30), nullable=False), sa.Column("node_name", sa.String(100)), sa.Column("config", sa.JSON(), nullable=False), sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"), sa.Column("parent_id", sa.Integer(), sa.ForeignKey("workflow_nodes.id")), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("task_records", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("workflow_defs.id"), nullable=False), sa.Column("data_source_id", sa.Integer(), sa.ForeignKey("data_sources.id"), nullable=False), sa.Column("status", sa.String(20), nullable=False, server_default="pending"), sa.Column("output_path", sa.String(500)), sa.Column("error_log", sa.Text()), sa.Column("started_at", sa.DateTime()), sa.Column("finished_at", sa.DateTime()))


def downgrade() -> None:
    op.drop_table("task_records")
    op.drop_table("workflow_nodes")
    op.drop_table("data_sources")
    op.drop_table("workflow_defs")
    op.drop_table("templates")
