from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any
from datetime import datetime
from bucket_harbour.domain.models import FileState

class TagUpdateRequest(BaseModel):
    tags: List[str]

class TransformRequest(BaseModel):
    func_name: str
    params: Dict[str, Any]

class AuditLogEntryResponse(BaseModel):
    id: str
    file_id: str
    command: str
    payload: Dict[str, Any]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class FileAggregateResponse(BaseModel):
    id: str
    current_state: FileState
    metadata_json: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)
