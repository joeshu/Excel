from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    has_formula: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    column_meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sheet_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[str] = mapped_column(String(30), default="1.0", nullable=False)
    parent_template_id: Mapped[int | None] = mapped_column(ForeignKey("templates.id"), nullable=True)
