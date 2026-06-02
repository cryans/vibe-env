from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import llm
import os
import json
import glob
from pathlib import Path
from typing import List, Optional
import datetime
import logging

from bucket_harbour.infrastructure.database import init_db
from bucket_harbour.presentation.routes import router as files_router

app = FastAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to stdout
        logging.FileHandler("backend.log")  # Log to a file
    ]
)

logger = logging.getLogger(__name__)

def format_exception_chain(exc: Exception) -> str:
    chain = []
    current = exc
    while current is not None:
        chain.append(f"{type(current).__name__}: {str(current)}")
        current = current.__cause__ or current.__context__
    return " -> ".join(chain)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    chain_str = format_exception_chain(exc)
    logger.error(
        f"HTTPException in route {request.method} {request.url.path}: "
        f"status_code={exc.status_code}, detail={exc.detail} | Exception Chain: {chain_str}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    chain_str = format_exception_chain(exc)
    logger.exception(
        f"Unhandled exception in route {request.method} {request.url.path}: "
        f"{str(exc)} | Exception Chain: {chain_str}"
    )
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {chain_str}"}
    )

@app.middleware("http")
async def files_exception_logging_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/files"):
        try:
            response = await call_next(request)
            if response.status_code >= 400:
                logger.error(
                    f"Error response {response.status_code} for files route: "
                    f"{request.method} {request.url.path}"
                )
            return response
        except Exception as exc:
            chain_str = format_exception_chain(exc)
            logger.exception(
                f"Unhandled exception in files route {request.method} "
                f"{request.url.path}: {str(exc)} | Exception Chain: {chain_str}"
            )
            raise exc
    return await call_next(request)

# Initialize DB on startup
@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(files_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODELS_FILE = Path("models.json")

def get_models_config() -> List[dict]:
    if not MODELS_FILE.exists():
        default_model = os.environ.get("LLM_MODEL", "gemini-1.5-flash")
        default_config = [
            {"model_id": default_model, "model_name": default_model.replace("-", " ").title(), "active": True},
            {"model_id": "gemini-1.5-pro", "model_name": "Gemini 1.5 Pro", "active": False},
            {"model_id": "gemini-1.5-flash-8b", "model_name": "Gemini 1.5 Flash 8B", "active": False}
        ]
        # Remove duplicates if default_model overlaps with hardcoded ones
        unique_config = []
        seen = set()
        for m in default_config:
            if m["model_id"] not in seen:
                seen.add(m["model_id"])
                unique_config.append(m)
        save_models_config(unique_config)
        return unique_config
    try:
        with open(MODELS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load models configuration from {MODELS_FILE}: {e}")
        return []

def save_models_config(config: List[dict]):
    try:
        with open(MODELS_FILE, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Models configuration saved to {MODELS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save models configuration to {MODELS_FILE}: {e}")

def get_active_model_config() -> Optional[dict]:
    config = get_models_config()
    for m in config:
        if m.get("active"):
            return m
    return None

def get_active_model() -> str:
    active_conf = get_active_model_config()
    if active_conf:
        return active_conf.get("model_id")
    return os.environ.get("LLM_MODEL", "Not configured")

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

class CommandRequest(BaseModel):
    command: str

class CommandResponse(BaseModel):
    response: str

class ModelItem(BaseModel):
    model_id: str
    model_name: str
    active: Optional[bool] = False
    log_path: Optional[str] = None
    custom: Optional[dict] = None

class LogRequest(BaseModel):
    level: str
    message: str
    timestamp: str

@app.post("/api/logs")
async def log_from_ui(request: LogRequest):
    log_entry = f"[{request.timestamp}] {request.level.upper()}: {request.message}\n"
    log_file_path = Path("ui_console.log")
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(log_entry)
    return {"status": "success"}

@app.post("/api/command", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    logger.info(f"Executing command: {request.command}")
    command = request.command.strip()
    
    if command == "!info":
        model_name = get_active_model()
        if model_name == "Not configured" or not model_name:
            return CommandResponse(response="No model configured.")
        
        try:
            model = llm.get_model(model_name)
            info_lines = [
                f"Configured Model: {model_name}",
                f"Model ID: {getattr(model, 'model_id', 'Unknown')}",
                f"Needs Key: {getattr(model, 'needs_key', 'Unknown')}",
                f"Can Stream: {getattr(model, 'can_stream', 'Unknown')}",
                f"Supports Vision: {getattr(model, 'vision', 'Unknown')}"
            ]
            return CommandResponse(response="\n".join(info_lines))
        except Exception as e:
            logger.error(f"Error retrieving model details for {model_name}: {e}")
            return CommandResponse(response=f"Configured Model: {model_name}\nError retrieving details: {str(e)}")
            
    return CommandResponse(response=f"Unknown command: {command}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info(f"Chat request received for session {request.session_id}: {request.message[:50]}...")
    active_conf = get_active_model_config()
    model_name = get_active_model()
    if not model_name or model_name == "Not configured":
        raise HTTPException(status_code=500, detail="LLM_MODEL not configured")
    
    try:
        model = llm.get_model(model_name)
        # Using Simon Willison's llm prompt method
        response = model.prompt(request.message)
        response_text = response.text()
        
        # Log to file if configured
        if active_conf and active_conf.get("log_path"):
            log_path_str = active_conf["log_path"]
            if request.session_id:
                log_path_str = log_path_str.replace("{session_id}", request.session_id)
            
            # Using JSONL for logging
            # To ensure it writes relative to the repo root and not backend folder when running in dev:
            actual_log_path = Path(log_path_str).expanduser()
            if not actual_log_path.is_absolute():
                actual_log_path = Path("/workspace") / actual_log_path
            actual_log_path.parent.mkdir(parents=True, exist_ok=True)
            
            log_entry = {
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "model_id": model_name,
                "session_id": request.session_id,
                "prompt": request.message,
                "response": response_text
            }
            with open(actual_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        return ChatResponse(response=response_text)
    except llm.UnknownModelError:
        logger.error(f"Unknown model error: {model_name}")
        raise HTTPException(status_code=500, detail=f"Unknown model: {model_name}")
    except Exception as e:
        logger.error(f"Error during chat for model {model_name}, session {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
async def get_models():
    # Return available models and configured one
    config = get_models_config()
    return {
        "configured_model": get_active_model(),
        "models": config
    }

@app.post("/api/models")
async def add_model(item: ModelItem):
    logger.info(f"Attempting to add model: {item.model_id}")
    config = get_models_config()
    if any(m.get("model_id") == item.model_id for m in config):
        logger.warning(f"Model {item.model_id} already exists.")
        raise HTTPException(status_code=400, detail="Model already exists")
    
    new_model = {
        "model_id": item.model_id, 
        "model_name": item.model_name, 
        "active": False,
        "log_path": item.log_path,
        "custom": item.custom or {}
    }
    if not config:
        new_model["active"] = True
    config.append(new_model)
    save_models_config(config)
    logger.info(f"Successfully added model: {new_model}")
    return {"status": "success", "model": new_model}

@app.put("/api/models/{model_id:path}")
async def update_model(model_id: str, item: ModelItem):
    logger.info(f"Attempting to update model: {model_id}")
    config = get_models_config()
    found = False
    for m in config:
        if m.get("model_id") == model_id:
            # We don't change 'active' status here, just config details
            m["model_name"] = item.model_name
            m["log_path"] = item.log_path
            m["custom"] = item.custom or {}
            # Update model_id if changed? Assuming we don't allow changing model_id here for simplicity
            # but if we do, we need to handle it. Let's keep model_id fixed for the PUT route target.
            found = True
            break
            
    if not found:
        logger.warning(f"Model {model_id} not found for update.")
        raise HTTPException(status_code=404, detail="Model not found")
        
    save_models_config(config)
    logger.info(f"Successfully updated model: {model_id}")
    return {"status": "success"}

@app.delete("/api/models/{model_id:path}")
async def delete_model(model_id: str):
    logger.info(f"Attempting to delete model: {model_id}")
    config = get_models_config()
    new_config = [m for m in config if m.get("model_id") != model_id]
    if len(new_config) == len(config):
        logger.warning(f"Model {model_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="Model not found")
    # If we deleted the active model, make the first one active if available
    if not any(m.get("active") for m in new_config) and new_config:
        new_config[0]["active"] = True
        logger.info(f"No active model found after deletion, set {new_config[0]['model_id']} as active.")
    save_models_config(new_config)
    logger.info(f"Successfully deleted model: {model_id}")
    return {"status": "success"}

@app.post("/api/models/select/{model_id:path}")
async def select_model(model_id: str):
    logger.info(f"Attempting to select model: {model_id}")
    config = get_models_config()
    found = False
    for m in config:
        if m.get("model_id") == model_id:
            m["active"] = True
            found = True
        else:
            m["active"] = False
    if not found:
        logger.warning(f"Model {model_id} not found for selection.")
        raise HTTPException(status_code=404, detail="Model not found")
    save_models_config(config)
    logger.info(f"Successfully selected model: {model_id}")
    return {"status": "success", "configured_model": model_id}

@app.get("/api/sessions")
async def get_sessions():
    logger.info("Fetching all sessions...")
    sessions = []
    
    # 1. Fetch from standard agent path
    base_dir = os.path.expanduser("/workspace/.pi/agent/sessions/--workspace--")
    if os.path.exists(base_dir):
        for file_path in glob.glob(f"{base_dir}/*.jsonl"):
            try:
                with open(file_path, "r") as f:
                    first_line = f.readline()
                    if first_line:
                        data = json.loads(first_line)
                        data["filename"] = os.path.basename(file_path)
                        data["filepath"] = file_path
                        data["source"] = "pi"
                        sessions.append(data)
            except Exception as e:
                logger.warning(f"Could not read session file {file_path} from standard path: {e}")
                pass
                
    # 2. Fetch from configured model log paths
    config = get_models_config()
    for m in config:
        if m.get("log_path") and "{session_id}" in m["log_path"]:
            pattern = m["log_path"].replace("{session_id}", "*")
            
            actual_pattern = Path(pattern).expanduser()
            if not actual_pattern.is_absolute():
                actual_pattern = Path("/workspace") / actual_pattern
                
            for file_path in glob.glob(str(actual_pattern)):
                try:
                    with open(file_path, "r") as f:
                        first_line = f.readline()
                        if first_line:
                            data = json.loads(first_line)
                            data["filename"] = os.path.basename(file_path)
                            data["filepath"] = file_path
                            data["source"] = "chat"
                            if "id" not in data:
                                # try to extract session_id from filename or just use filename
                                data["id"] = data["filename"]
                            # Create a small title preview
                            if data.get("prompt"):
                                data["title"] = data["prompt"][:30] + ("..." if len(data["prompt"]) > 30 else "")
                            
                            # Only add if we haven't already (prevent duplicates)
                            if not any(s.get("filepath") == file_path for s in sessions):
                                sessions.append(data)
                except Exception as e:
                    logger.warning(f"Could not read session file {file_path} from custom log path: {e}")
                    pass
                    
    logger.info(f"Found {len(sessions)} sessions.")
    return sorted(sessions, key=lambda x: x.get("timestamp", ""), reverse=True)

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    logger.info(f"Fetching session details for: {session_id}")
    # First check standard path
    base_dir = os.path.expanduser("/workspace/.pi/agent/sessions/--workspace--")
    file_path = os.path.join(base_dir, session_id)
    
    # If not found, look up through config globs
    if not os.path.exists(file_path):
        found_file = None
        
        # Check standard base dir globs
        if os.path.exists(base_dir):
            for fp in glob.glob(f"{base_dir}/*.jsonl"):
                if session_id in fp:
                    found_file = fp
                    break
                    
        # Check custom log paths
        if not found_file:
            config = get_models_config()
            for m in config:
                if m.get("log_path") and "{session_id}" in m["log_path"]:
                    pattern = m["log_path"].replace("{session_id}", "*")
                    actual_pattern = Path(pattern).expanduser()
                    if not actual_pattern.is_absolute():
                        actual_pattern = Path("/workspace") / actual_pattern
                    
                    for fp in glob.glob(str(actual_pattern)):
                        if session_id in fp:
                            found_file = fp
                            break
                if found_file:
                    break
                    
        if not found_file:
            raise HTTPException(status_code=404, detail="Session not found")
        file_path = found_file

    lines = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                lines.append(json.loads(line))
        logger.info(f"Successfully loaded session {session_id} with {len(lines)} entries.")
        return {"session": lines}
    except Exception as e:
        logger.error(f"Error reading session file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
