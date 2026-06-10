from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from datetime import datetime
from sqlalchemy.orm import Session
from bucket_harbour.infrastructure.database import get_db
from bucket_harbour.domain.models import FileState
from bucket_harbour.infrastructure.file_service import FileService
from bucket_harbour.application.file_application_service import FileApplicationService
from bucket_harbour.presentation.schemas import (
    FileAggregateResponse, TagUpdateRequest, TransformRequest, AuditLogEntryResponse
)

router = APIRouter(prefix="/api/files", tags=["files"])
file_service_instance = FileService()

def get_file_application_service(db: Session = Depends(get_db)) -> FileApplicationService:
    return FileApplicationService(db, file_service_instance)

@router.post("/stage", response_model=FileAggregateResponse)
def stage_file(file: UploadFile = File(...), service: FileApplicationService = Depends(get_file_application_service)):
    try:
        return service.stage_file(file.filename, file.content_type, file.file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stage file: {str(e)}")

@router.patch("/{id}/tags", response_model=FileAggregateResponse)
def update_tags(id: str, payload: TagUpdateRequest, service: FileApplicationService = Depends(get_file_application_service)):
    try:
        return service.update_tags(id, payload.tags)
    except ValueError as e:
        raise HTTPException(status_code=400 if "modify" in str(e) else 404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{id}/transform", response_model=FileAggregateResponse)
def transform_file(id: str, payload: TransformRequest, service: FileApplicationService = Depends(get_file_application_service)):
    try:
        return service.transform_file(id, payload.func_name, payload.params)
    except ValueError as e:
        raise HTTPException(status_code=400 if "modify" in str(e) else 404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{id}/commit", response_model=FileAggregateResponse)
def commit_file(id: str, service: FileApplicationService = Depends(get_file_application_service)):
    try:
        return service.commit_file(id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to commit file: {str(e)}")

@router.post("/{id}/discard", response_model=FileAggregateResponse)
def discard_file(id: str, service: FileApplicationService = Depends(get_file_application_service)):
    try:
        return service.discard_file(id)
    except ValueError as e:
        raise HTTPException(status_code=400 if "already PERSISTED" in str(e) else 404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discard file: {str(e)}")

@router.get("/{id}/audit", response_model=list[AuditLogEntryResponse])
def get_audit_log(id: str, service: FileApplicationService = Depends(get_file_application_service)):
    file_agg = service.get_file_aggregate_by_id(id)
    if not file_agg:
        raise HTTPException(status_code=404, detail="File not found")
        
    return file_agg.audit_logs

@router.get("/{id}/download")
def get_download_link(id: str, service: FileApplicationService = Depends(get_file_application_service)):
    file_agg = service.get_file_aggregate_by_id(id)
    if not file_agg:
        raise HTTPException(status_code=404, detail="File not found")
        
    if file_agg.current_state != FileState.PERSISTED:
        raise HTTPException(status_code=400, detail="File is not persisted yet")
        
    try:
        url = service.generate_presigned_url(id)
        return {"download_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")

@router.get("/staged", response_model=list[str])
def get_staged_files(service: FileApplicationService = Depends(get_file_application_service)):
    files = service.get_files_by_state(FileState.STAGED)
    return [f.id for f in files]

@router.get("/persisted", response_model=list[str])
def get_persisted_files(service: FileApplicationService = Depends(get_file_application_service)):
    files = service.get_files_by_state(FileState.PERSISTED)
    return [f.id for f in files]

@router.get("/events/{id}")
def get_file_events(id: str, service: FileApplicationService = Depends(get_file_application_service)):
    file_agg = service.get_file_aggregate_by_id(id)
    if not file_agg:
        raise HTTPException(status_code=404, detail="File not found")
    
    events = []
    for log in file_agg.audit_logs:
        events.append({
            "timestamp": log.timestamp.isoformat() if log.timestamp else datetime.utcnow().isoformat(),
            "eventType": log.command,
            "payload": log.payload
        })
    return events

@router.post("/{id}/replay", response_model=FileAggregateResponse)
def replay_file_events(id: str, service: FileApplicationService = Depends(get_file_application_service)):
    try:
        return service.reconstruct_from_history(id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{id}")
def download_file_direct(id: str, service: FileApplicationService = Depends(get_file_application_service)):
    file_agg = service.get_file_aggregate_by_id(id)
    if not file_agg:
        raise HTTPException(status_code=404, detail="File not found")
        
    if file_agg.current_state != FileState.PERSISTED:
        raise HTTPException(status_code=400, detail="File is not persisted yet")
        
    try:
        url = service.generate_presigned_url(id)
        return RedirectResponse(url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")
