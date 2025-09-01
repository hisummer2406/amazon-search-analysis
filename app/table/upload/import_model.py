from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, Integer, String, Date, Boolean, Text, DateTime, Numeric, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date
from typing import Optional
import enum

from database import Base


class StatusEnum(enum.Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ImportBatchRecords(Base):
    __tablename__ = "import_batch_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_name: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    import_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[StatusEnum] = mapped_column(SQLEnum(StatusEnum, name="status_enum", schema="analysis"),
                                               nullable=False)
    processed_keywords: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processing_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_day_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_week_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, server_default=func.now(),
                                                             onupdate=func.now())


