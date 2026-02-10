from sqlalchemy import String, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .db import Base


class IngestionBatch(Base):
    __tablename__ = "ingestion_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), default="gdelt")
    file_url: Mapped[str] = mapped_column(Text)
    file_ts: Mapped[str] = mapped_column(String(20))  # YYYYMMDDHHMMSS
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued|done|failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
