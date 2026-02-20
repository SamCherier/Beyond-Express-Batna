from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import logging

from services.ai_orchestrator import orchestrator, AGENTS

logger = logging.getLogger(__name__)
router = APIRouter()


def _db():
    from server import db
    return db

async def _auth(request):
    from auth_utils import verify_token
    from models import User
    db = _db()
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    sess = await db.sessions.find_one({"session_token": token}, {"_id": 0})
    if sess:
        if datetime.fromisoformat(sess['expires_at']) > datetime.now(timezone.utc):
            user_doc = await db.users.find_one({"id": sess['user_id']}, {"_id": 0})
            if user_doc:
                return User(**user_doc)
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_doc = await db.users.find_one({"id": payload.get("sub")}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user_doc)


# ── Models ──

class ConfigureRequest(BaseModel):
    api_key: Optional[str] = None
    provider: str = "openrouter"
    model: str = "qwen/qwen3-30b-a3b:free"
    enabled: bool = True

class QueryRequest(BaseModel):
    agent_id: str
    task: str


# ── Routes ──

@router.get("/status")
async def get_brain_status(request: Request):
    await _auth(request)
    status = orchestrator.get_status()
    # Security: Never expose any part of API keys - just indicate presence
    # has_api_key is already a boolean indicator
    # Remove any system prompts from agent data to reduce response size
    if "agents" in status:
        for agent in status["agents"]:
            if "system_prompt" in agent:
                del agent["system_prompt"]
    return status


@router.post("/configure")
async def configure_brain(data: ConfigureRequest, request: Request):
    user = await _auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    orchestrator.configure(
        api_key=data.api_key if data.api_key else None,
        provider=data.provider,
        model=data.model,
        enabled=data.enabled,
    )

    # Persist config to DB
    db = _db()
    await db.ai_brain_config.update_one(
        {"key": "main"},
        {"$set": {
            "provider": data.provider,
            "model": data.model,
            "enabled": data.enabled,
            "has_api_key": bool(data.api_key),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.id,
        }},
        upsert=True,
    )

    return {"message": "Configuration mise à jour", "status": orchestrator.get_status()}


@router.post("/query")
async def query_agent(data: QueryRequest, request: Request):
    await _auth(request)

    if not orchestrator.enabled:
        raise HTTPException(status_code=503, detail="AI Brain is disabled")

    result = await orchestrator.query_agent(data.agent_id, data.task)

    # Log the query
    db = _db()
    await db.ai_brain_logs.insert_one({
        "agent_id": data.agent_id,
        "task": data.task,
        "is_simulated": result.get("is_simulated", True),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "_id_skip": True,
    })

    return result


@router.get("/agents")
async def list_agents(request: Request):
    await _auth(request)
    return list(AGENTS.values())


@router.get("/logs")
async def get_brain_logs(request: Request):
    user = await _auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    db = _db()
    logs = await db.ai_brain_logs.find({}, {"_id": 0, "_id_skip": 0}).sort("timestamp", -1).to_list(50)
    return logs
