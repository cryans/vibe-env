import uuid
import datetime
from enum import Enum
from typing import Any, Dict, List

from sqlalchemy import String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class FileState(str, Enum):
    STAGED = "STAGED"
    PERSISTED = "PERSISTED"


class FileAggregate(Base):
    __tablename__ = "file_aggregates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    current_state: Mapped[FileState] = mapped_column(String(20), default=FileState.STAGED)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    audit_logs: Mapped[List["AuditLogEntry"]] = relationship(
        "AuditLogEntry", 
        back_populates="file", 
        cascade="all, delete-orphan", 
        order_by="AuditLogEntry.timestamp"
    )


class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id: Mapped[str] = mapped_column(ForeignKey("file_aggregates.id"), nullable=False)
    command: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    
    file: Mapped["FileAggregate"] = relationship("FileAggregate", back_populates="audit_logs")
