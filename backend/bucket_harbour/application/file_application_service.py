
from typing import BinaryIO, List, Optional, Protocol, Tuple
from sqlalchemy.orm import Session
from bucket_harbour.domain.models import FileAggregate, AuditLogEntry, FileState # Assuming Base is also in models
import uuid # Import uuid for event_id generation

# Define the FileService Protocol
class IFileService(Protocol):
    def save_to_staging(self, file_id: str, file_stream: BinaryIO) -> Tuple[str, str]:
        """Saves file stream to staging, returns staging path and checksum."""
        ...
    
    def upload_to_s3(self, file_id: str, checksum: str) -> str:
        """Uploads staged file to S3, returns final checksum."""
        ...

class FileApplicationService:
    # Type hint file_service with the protocol IFileService
    def __init__(self, db: Session, file_service: IFileService):
        self.db = db
        self.file_service: IFileService = file_service # Explicitly type hint

    def _get_previous_event_id(self, file_id: str) -> Optional[str]:
        """Fetches the event_id of the most recent audit log entry for a given file.
        Returns None if no previous events exist for the file.
        """
        latest_log = self.db.query(AuditLogEntry)\
        .filter(AuditLogEntry.file_id == file_id)\
        .order_by(AuditLogEntry.timestamp.desc())\
        .first()
        return latest_log.event_id if latest_log else None

    def stage_file(self, filename: str, content_type: str, file_stream: BinaryIO) -> FileAggregate:
        """Orchestrates the staging of a file and records the STAGE_EVENT."""
        file_id = str(uuid.uuid4())
        file_agg = FileAggregate(id=file_id, entity_id=file_id)
        if file_agg.metadata_json is None:
            file_agg.metadata_json = {}
        self.db.add(file_agg)

        try:
            # 1. Save file stream and calculate SHA-256 on the fly
            filepath, checksum = self.file_service.save_to_staging(file_agg.id, file_stream)
        except Exception as e:
            self.db.rollback()
            raise e

        # Manually update metadata_json with required fields.
        file_agg.metadata_json["filename"] = filename
        file_agg.metadata_json["content_type"] = content_type
        file_agg.metadata_json["checksum"] = checksum

        # 2. Apply stage event to transition state.
        # The payload for the event/audit log.
        event_payload = {"filename": filename, "content_type": content_type, "checksum": checksum}
        file_agg.apply_event("STAGE_EVENT", event_payload)

        # 3. Create the persistent audit log entry
        previous_event_id = self._get_previous_event_id(file_agg.id) # This will be None for a new file
        audit_log = AuditLogEntry(
            file_id=file_agg.id, 
            entity_id=file_agg.id,
            command="STAGE_EVENT", 
            payload=event_payload, 
            event_id=str(uuid.uuid4()), 
            previous_event_id=previous_event_id
        )
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
        
        previous_event_id = self._get_previous_event_id(file_id)
        audit_log = AuditLogEntry(
            file_id=file_id, 
            entity_id=file_agg.entity_id,
            command="TAG_UPDATE", 
            payload=payload, 
            event_id=str(uuid.uuid4()), 
            previous_event_id=previous_event_id
        )
        self.db.add(audit_log)
        
        self.db.commit()
        self.db.refresh(file_agg)
        return file_agg

    def transform_file(self, file_id: str, func_name: str, params: dict) -> FileAggregate:
        file_agg = self.db.query(FileAggregate).filter(FileAggregate.id == file_id).first()
        if not file_agg:
            raise ValueError("File not found")

        # Define the transformation payload data.
        transform_data = {"func_name": func_name, "params": params}
        
        # Manually update metadata_json with the expected nested structure.
        file_agg.metadata_json["transform_params"] = transform_data

        # Apply the event and create the audit log entry using this data.
        event_payload = transform_data
        file_agg.apply_event("TRANSFORM", event_payload)

        previous_event_id = self._get_previous_event_id(file_id)
        audit_log = AuditLogEntry(
            file_id=file_id, 
            entity_id=file_agg.entity_id,
            command="TRANSFORM", 
            payload=event_payload, 
            event_id=str(uuid.uuid4()), 
            previous_event_id=previous_event_id
        )
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
        existing_checksum = file_agg.metadata_json.get("checksum")
        if not existing_checksum:
             raise ValueError(f"File {file_id} has no checksum metadata, cannot commit.")
             
        try:
            checksum = self.file_service.upload_to_s3(file_id, checksum=existing_checksum)
        except Exception as e:
            self.db.rollback()
            raise e

        # 2. Transition state and commit
        payload = {"s3_key": file_id, "checksum": checksum}
        file_agg.apply_event("COMMIT_EVENT", payload)

        previous_event_id = self._get_previous_event_id(file_id)
        audit_log = AuditLogEntry(
            file_id=file_id, 
            entity_id=file_agg.entity_id,
            command="COMMIT_EVENT", 
            payload=payload, 
            event_id=str(uuid.uuid4()), 
            previous_event_id=previous_event_id
        )
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
        
        previous_event_id = self._get_previous_event_id(file_id)
        audit_log = AuditLogEntry(
            file_id=file_id, 
            entity_id=file_agg.entity_id,
            command="DISCARD_EVENT", 
            payload=payload, 
            event_id=str(uuid.uuid4()), 
            previous_event_id=previous_event_id
        )
        self.db.add(audit_log)
        
        self.db.commit()
        self.db.refresh(file_agg)
        return file_agg

    def reconstruct_from_history(self, file_id: str) -> FileAggregate:
        """Reconstructs or validates an Aggregate's state by replaying its history."""
        file_agg = self.db.query(FileAggregate).filter(FileAggregate.id == file_id).first()
        if not file_agg:
            raise ValueError("File not found")
        
        # Fetch all audit logs for this file, ordered by timestamp
        # Note: The order_by(AuditLogEntry.timestamp) ensures replay order.
        # We assume event_id and previous_event_id are correctly set upon creation.
        audit_logs = self.db.query(AuditLogEntry).filter(AuditLogEntry.file_id == file_id).order_by(AuditLogEntry.timestamp).all()
        
        file_agg.replay_events(audit_logs)
        return file_agg

    def get_files_by_state(self, file_state: str) -> List[FileAggregate]: # Changed type hint to str for consistency with tests
        return self.db.query(FileAggregate).filter(FileAggregate.current_state == file_state).all()

    def get_file_aggregate_by_id(self, id: str) -> FileAggregate:
        return self.db.query(FileAggregate).filter(FileAggregate.id == id).first()
