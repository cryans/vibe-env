from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.domain.models import FileAggregate, AuditLogEntry, FileState
from src.infrastructure.file_service import FileService
from src.presentation.schemas import (
    FileAggregateResponse, TagUpdateRequest, TransformRequest, AuditLogEntryResponse
)

router = APIRouter(prefix="/files", tags=["files"])
file_service = FileService()

@router.post("/stage", response_model=FileAggregateResponse)
def stage_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_agg = FileAggregate(
        current_state=FileState.STAGED,
        metadata_json={"orig_name": file.filename, "tags": []}
    )
    db.add(file_agg)
    db.flush()
    
    try:
        file_service.save_to_staging(file_agg.id, file.file)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to stage file: {str(e)}")
        
    audit_log = AuditLogEntry(
        file_id=file_agg.id,
        command="STAGE_EVENT",
        payload={"filename": file.filename, "content_type": file.content_type}
    )
    db.add(audit_log)
    db.commit()
    db.refresh(file_agg)
    
    return file_agg

@router.patch("/{id}/tags", response_model=FileAggregateResponse)
def update_tags(id: str, payload: TagUpdateRequest, db: Session = Depends(get_db)):
    file_agg = db.query(FileAggregate).filter(FileAggregate.id == id).first()
    if not file_agg:
        raise HTTPException(status_code=404, detail="File not found")
        
    if file_agg.current_state == FileState.PERSISTED:
        raise HTTPException(status_code=400, detail="Cannot modify a PERSISTED file")
        
    metadata = dict(file_agg.metadata_json)
    metadata["tags"] = payload.tags
    file_agg.metadata_json = metadata
    
    audit_log = AuditLogEntry(
        file_id=id,
        command="TAG_UPDATE",
        payload={"tags": payload.tags}
    )
    db.add(audit_log)
    db.commit()
    db.refresh(file_agg)
    
    return file_agg

@router.post("/{id}/transform", response_model=FileAggregateResponse)
def transform_file(id: str, payload: TransformRequest, db: Session = Depends(get_db)):
    file_agg = db.query(FileAggregate).filter(FileAggregate.id == id).first()
    if not file_agg:
        raise HTTPException(status_code=404, detail="File not found")
        
    if file_agg.current_state == FileState.PERSISTED:
        raise HTTPException(status_code=400, detail="Cannot modify a PERSISTED file")
        
    metadata = dict(file_agg.metadata_json)
    transformations = metadata.get("transformations", [])
    transformations.append({"func_name": payload.func_name, "params": payload.params})
    metadata["transformations"] = transformations
    file_agg.metadata_json = metadata
    
    audit_log = AuditLogEntry(
        file_id=id,
        command="TRANSFORM",
        payload={"func_name": payload.func_name, "params": payload.params}
    )
    db.add(audit_log)
    db.commit()
    db.refresh(file_agg)
    
    return file_agg

@router.post("/{id}/commit", response_model=FileAggregateResponse)
def commit_file(id: str, db: Session = Depends(get_db)):
    file_agg = db.query(FileAggregate).filter(FileAggregate.id == id).first()
    if not file_agg:
        raise HTTPException(status_code=404, detail="File not found")
        
    if file_agg.current_state == FileState.PERSISTED:
        return file_agg
        
    try:
        checksum = file_service.upload_to_s3(id)
        
        file_agg.current_state = FileState.PERSISTED
        metadata = dict(file_agg.metadata_json)
        metadata["sha256"] = checksum
        file_agg.metadata_json = metadata
        
        audit_log = AuditLogEntry(
            file_id=id,
            command="COMMIT_EVENT",
            payload={"s3_key": id, "checksum": checksum}
        )
        db.add(audit_log)
        
        db.commit()
        db.refresh(file_agg)
        return file_agg
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to commit file: {str(e)}")

@router.get("/{id}/audit", response_model=list[AuditLogEntryResponse])
def get_audit_log(id: str, db: Session = Depends(get_db)):
    file_agg = db.query(FileAggregate).filter(FileAggregate.id == id).first()
    if not file_agg:
        raise HTTPException(status_code=404, detail="File not found")
        
    return file_agg.audit_logs

@router.get("/{id}/download")
def get_download_link(id: str, db: Session = Depends(get_db)):
    file_agg = db.query(FileAggregate).filter(FileAggregate.id == id).first()
    if not file_agg:
        raise HTTPException(status_code=404, detail="File not found")
        
    if file_agg.current_state != FileState.PERSISTED:
        raise HTTPException(status_code=400, detail="File is not persisted yet")
        
    try:
        url = file_service.generate_presigned_url(id)
        return {"download_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")
