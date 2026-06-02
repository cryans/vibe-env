from typing import BinaryIO, List, Optional
from sqlalchemy.orm import Session
from bucket_harbour.domain.models import FileAggregate, AuditLogEntry, FileState
from bucket_harbour.infrastructure.file_service import FileService

class FileApplicationService:
    def __init__(self, db: Session, file_service: FileService):
        self.db = db
        self.file_service = file_service

    def stage_file(self, filename: str, content_type: str, file_stream: BinaryIO) -> FileAggregate:
        """Orchestrates the staging of a file and records the STAGE_EVENT."""
        file_agg = FileAggregate()
        self.db.add(file_agg)
        self.db.flush()  # Generates the file_agg.id UUID

        try:
            # 1. Save file stream and calculate SHA-256 on the fly
            filepath, checksum = self.file_service.save_to_staging(file_agg.id, file_stream)
        except Exception as e:
            self.db.rollback()
            raise e

        # 2. Apply stage event to transition state & save SHA-256
        payload = {"filename": filename, "content_type": content_type, "sha256": checksum}
        file_agg.apply_event("STAGE_EVENT", payload)

        # 3. Create the persistent audit log entry
        audit_log = AuditLogEntry(file_id=file_agg.id, command="STAGE_EVENT", payload=payload)
        self.db.add(audit_log)
        
        self.db.commit()
        self.db.refresh(file_agg)
        return file_agg

    def update_tags(self, file_id: str, tags: List[str]) -> FileAggregate:
        file_agg = self.db.query(FileAggregate).filter(FileAggregate.id == file_id).first()
        if not file_agg:
            raise ValueError("File not found")

        payload = {"tags": tags}
        file_agg.apply_event("TAG_UPDATE", payload)
        
        audit_log = AuditLogEntry(file_id=file_id, command="TAG_UPDATE", payload=payload)
        self.db.add(audit_log)
        
        self.db.commit()
        self.db.refresh(file_agg)
        return file_agg

    def transform_file(self, file_id: str, func_name: str, params: dict) -> FileAggregate:
        file_agg = self.db.query(FileAggregate).filter(FileAggregate.id == file_id).first()
        if not file_agg:
            raise ValueError("File not found")

        payload = {"func_name": func_name, "params": params}
        file_agg.apply_event("TRANSFORM", payload)
        
        audit_log = AuditLogEntry(file_id=file_id, command="TRANSFORM", payload=payload)
        self.db.add(audit_log)
        
        self.db.commit()
        self.db.refresh(file_agg)
        return file_agg

    def commit_file(self, file_id: str) -> FileAggregate:
        file_agg = self.db.query(FileAggregate).filter(FileAggregate.id == file_id).first()
        if not file_agg:
            raise ValueError("File not found")
        if file_agg.current_state == FileState.PERSISTED:
            return file_agg

        # 1. Upload to S3 using the pre-calculated sha256 checksum
        existing_checksum = file_agg.metadata_json.get("sha256")
        try:
            checksum = self.file_service.upload_to_s3(file_id, checksum=existing_checksum)
        except Exception as e:
            self.db.rollback()
            raise e

        # 2. Transition state and commit
        payload = {"s3_key": file_id, "checksum": checksum}
        file_agg.apply_event("COMMIT_EVENT", payload)

        audit_log = AuditLogEntry(file_id=file_id, command="COMMIT_EVENT", payload=payload)
        self.db.add(audit_log)

        self.db.commit()
        self.db.refresh(file_agg)
        return file_agg

    def discard_file(self, file_id: str) -> FileAggregate:
        file_agg = self.db.query(FileAggregate).filter(FileAggregate.id == file_id).first()
        if not file_agg:
            raise ValueError("File not found")
        if file_agg.current_state == FileState.DISCARDED:
            return file_agg

        payload = {}
        file_agg.apply_event("DISCARD_EVENT", payload)
        
        audit_log = AuditLogEntry(file_id=file_id, command="DISCARD_EVENT", payload=payload)
        self.db.add(audit_log)
        
        self.db.commit()
        self.db.refresh(file_agg)
        return file_agg

    def reconstruct_from_history(self, file_id: str) -> FileAggregate:
        """Reconstructs or validates an Aggregate's state by replaying its history."""
        file_agg = self.db.query(FileAggregate).filter(FileAggregate.id == file_id).first()
        if not file_agg:
            raise ValueError("File not found")
        
        file_agg.replay_events(file_agg.audit_logs)
        return file_agg

    def get_files_by_state(self, file_state: FileState) -> List[FileAggregate]:
        return self.db.query(FileAggregate).filter(FileAggregate.current_state == file_state).all()

    def get_file_aggregate_by_id(self, id: str) -> FileAggregate:
        return self.db.query(FileAggregate).filter(FileAggregate.id == id).first()
