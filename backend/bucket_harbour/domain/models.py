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
    DISCARDED = "DISCARDED"


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

    def apply_event(self, command: str, payload: dict) -> None:
        """
        The ONLY way state changes inside FileAggregate.
        Applies a single domain event/command to transition the aggregate state.
        """
        if command == "STAGE_EVENT":
            self.current_state = FileState.STAGED
            self.metadata_json = {
                "orig_name": payload.get("filename"),
                "tags": [],
                "sha256": payload.get("sha256")
            }
            
        elif command == "TAG_UPDATE":
            if self.current_state == FileState.PERSISTED:
                raise ValueError("Cannot modify a PERSISTED file")
            self.metadata_json = {
                **self.metadata_json,
                "tags": payload.get("tags", [])
            }
            
        elif command == "TRANSFORM":
            if self.current_state == FileState.PERSISTED:
                raise ValueError("Cannot modify a PERSISTED file")
            transformations = list(self.metadata_json.get("transformations", []))
            transformations.append({
                "func_name": payload.get("func_name"),
                "params": payload.get("params")
            })
            self.metadata_json = {
                **self.metadata_json,
                "transformations": transformations
            }
            
        elif command == "COMMIT_EVENT":
            self.current_state = FileState.PERSISTED
            self.metadata_json = {
                **self.metadata_json,
                "sha256": payload.get("checksum")
            }
            
        elif command == "DISCARD_EVENT":
            if self.current_state == FileState.PERSISTED:
                raise ValueError("Cannot discard a file that is already PERSISTED")
            self.current_state = FileState.DISCARDED
            
        else:
            raise ValueError(f"Unknown event command: {command}")

    def replay_events(self, events: List["AuditLogEntry"]) -> None:
        """
        Reconstructs the aggregate's state from scratch by replaying its historical event log.
        """
        self.current_state = None
        self.metadata_json = {}
        
        # Ensure events are ordered by their timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        for event in sorted_events:
            self.apply_event(event.command, event.payload)



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
