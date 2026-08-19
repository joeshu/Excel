from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TemplateWorkbookProfile(Base):
    __tablename__ = "template_workbook_profiles"
    __table_args__ = (UniqueConstraint("template_id", name="uq_template_workbook_profile_template"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id", ondelete="CASCADE"), nullable=False, index=True)
    profile: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    validation_result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
