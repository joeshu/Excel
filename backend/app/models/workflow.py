from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WorkflowDef(Base):
    __tablename__ = "workflow_defs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    node_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    column_mapping: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    notice_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    notice_config_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notice_config_history: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_example: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    applicable_field_signature: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow_defs.id", ondelete="CASCADE"), nullable=False)
    node_type: Mapped[str] = mapped_column(String(30), nullable=False)
    node_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_nodes.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
