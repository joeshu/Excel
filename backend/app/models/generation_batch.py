from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GenerationBatch(Base):
    __tablename__ = "generation_batches"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow_defs.id"), nullable=False)
    notice_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
