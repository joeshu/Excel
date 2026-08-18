from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    schema_: Mapped[dict] = mapped_column("schema", JSON, default=dict, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    connection_info: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_example: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    field_signature: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    data_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quality_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
