from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MappingSnapshot(Base):
    __tablename__ = "mapping_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow_defs.id"), nullable=False, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"), nullable=False)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    template_version: Mapped[str] = mapped_column(String(30), nullable=False)
    data_field_signature: Mapped[str] = mapped_column(String(500), nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    rules: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    dependency_order: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    validation_result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
