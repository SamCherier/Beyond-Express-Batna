"""
AI Configuration — Multi-Provider / Multi-Agent Matrix
Manages API keys for multiple providers and assigns models to agents.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, timezone
import httpx
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

PROVIDERS = {
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "env_key": "OPENROUTER_API_KEY",
        "models": [
            {"id": "meta-llama/llama-3.3-70b-instruct:free", "label": "Llama 3.3 70B (Gratuit)"},
            {"id": "qwen/qwen3-4b:free", "label": "Qwen 3 4B (Gratuit)"},
            {"id": "deepseek/deepseek-r1-0528:free", "label": "DeepSeek R1 (Gratuit)"},
            {"id": "google/gemma-3-27b-it:free", "label": "Gemma 3 27B (Gratuit)"},
        ],
        "headers_extra": {"HTTP-Referer": "https://beyondexpress.dz", "X-Title": "Beyond Express"},
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "env_key": "GROQ_API_KEY",
        "models": [
            {"id": "llama-3.3-70b-versatile", "label": "Llama 3.3 70B"},
            {"id": "mixtral-8x7b-32768", "label": "Mixtral 8x7B"},
            {"id": "gemma2-9b-it", "label": "Gemma 2 9B"},
        ],
        "headers_extra": {},
    },
    "together": {
        "name": "Together AI",
        "base_url": "https://api.together.xyz/v1/chat/completions",
        "env_key": "TOGETHER_API_KEY",
        "models": [
            {"id": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "label": "Llama 3.3 70B Turbo"},
            {"id": "Qwen/Qwen2.5-72B-Instruct-Turbo", "label": "Qwen 2.5 72B"},
            {"id": "mistralai/Mixtral-8x7B-Instruct-v0.1", "label": "Mixtral 8x7B"},
        ],
        "headers_extra": {},
    },
    "moonshot": {
        "name": "Moonshot / Kimi",
        "base_url": "https://api.moonshot.cn/v1/chat/completions",
        "env_key": "MOONSHOT_API_KEY",
        "models": [
            {"id": "moonshot-v1-8k", "label": "Moonshot V1 8K"},
            {"id": "moonshot-v1-32k", "label": "Moonshot V1 32K"},
        ],
        "headers_extra": {},
    },
}

DEFAULT_AGENT_MATRIX = {
    "logistician": {"provider": "openrouter", "model": "meta-llama/llama-3.3-70b-instruct:free"},
    "analyst": {"provider": "openrouter", "model": "meta-llama/llama-3.3-70b-instruct:free"},
    "monitor": {"provider": "openrouter", "model": "meta-llama/llama-3.3-70b-instruct:free"},
}


def _db():
    from server import db
    return db


async def _auth(request):
    from auth_utils import verify_token
    from models import User
    db = _db()
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.sessions.find_one({"session_token": token}, {"_id": 0})
    if session:
        from datetime import datetime as dt
        if dt.fromisoformat(session["expires_at"]) > datetime.now(timezone.utc):
            user_doc = await db.users.find_one({"id": session["user_id"]}, {"_id": 0})
            if user_doc:
                return User(**user_doc)
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_doc = await db.users.find_one({"id": payload.get("sub")}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user_doc)


class SaveProviderKey(BaseModel):
    provider: str
    api_key: str


class UpdateAgentModel(BaseModel):
    agent_id: str
    provider: str
    model: str


class TestProviderRequest(BaseModel):
    provider: str


@router.get("/providers")
async def list_providers(request: Request):
    """List all available providers with their models and connection status."""
    await _auth(request)
    db = _db()

    stored = await db.ai_provider_keys.find({}, {"_id": 0}).to_list(100)
    stored_map = {s["provider"]: s for s in stored}

    result = []
    for pid, pinfo in PROVIDERS.items():
        s = stored_map.get(pid, {})
        key = s.get("api_key", "")
        result.append({
            "id": pid,
            "name": pinfo["name"],
            "models": pinfo["models"],
            "has_key": bool(key),
            "key_masked": ("*" * (len(key) - 4) + key[-4:]) if len(key) > 4 else "",
            "last_tested": s.get("last_tested"),
            "test_status": s.get("test_status"),
        })
    return result


@router.post("/providers/save-key")
async def save_provider_key(req: SaveProviderKey, request: Request):
    """Save or update an API key for a provider."""
    await _auth(request)
    db = _db()

    if req.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Provider inconnu: {req.provider}")

    await db.ai_provider_keys.update_one(
        {"provider": req.provider},
        {"$set": {
            "provider": req.provider,
            "api_key": req.api_key,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    # Also update the orchestrator if it's openrouter
    if req.provider == "openrouter":
        import os
        os.environ["OPENROUTER_API_KEY"] = req.api_key
        from services.ai_orchestrator import orchestrator
        orchestrator.api_key = req.api_key
        orchestrator.provider = "openrouter"
        orchestrator._init_client()

    return {"success": True, "message": f"Clé {PROVIDERS[req.provider]['name']} sauvegardée"}


@router.post("/providers/test")
async def test_provider(req: TestProviderRequest, request: Request):
    """Test connection to a provider."""
    await _auth(request)
    db = _db()

    if req.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Provider inconnu: {req.provider}")

    stored = await db.ai_provider_keys.find_one({"provider": req.provider}, {"_id": 0})
    if not stored or not stored.get("api_key"):
        return {"success": False, "error": f"Aucune clé configurée pour {PROVIDERS[req.provider]['name']}"}

    pinfo = PROVIDERS[req.provider]
    api_key = stored["api_key"]
    test_model = pinfo["models"][0]["id"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        **pinfo.get("headers_extra", {}),
    }
    payload = {
        "model": test_model,
        "messages": [{"role": "user", "content": "Dis bonjour en une phrase."}],
        "max_tokens": 50,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(pinfo["base_url"], headers=headers, json=payload)

        now = datetime.now(timezone.utc).isoformat()

        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            await db.ai_provider_keys.update_one(
                {"provider": req.provider},
                {"$set": {"last_tested": now, "test_status": "ok"}},
            )
            return {
                "success": True,
                "provider": pinfo["name"],
                "model": test_model,
                "response": content[:200],
            }
        else:
            error_text = resp.text[:200]
            await db.ai_provider_keys.update_one(
                {"provider": req.provider},
                {"$set": {"last_tested": now, "test_status": "error"}},
            )
            return {"success": False, "error": f"HTTP {resp.status_code}: {error_text}"}

    except httpx.TimeoutException:
        return {"success": False, "error": "Timeout — le serveur n'a pas répondu"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/agent-matrix")
async def get_agent_matrix(request: Request):
    """Get the current agent-to-model assignment matrix."""
    await _auth(request)
    db = _db()

    matrix = await db.ai_agent_matrix.find_one({"_id": "matrix"})
    if matrix:
        matrix.pop("_id", None)
        return matrix.get("agents", DEFAULT_AGENT_MATRIX)
    return DEFAULT_AGENT_MATRIX


@router.post("/agent-matrix")
async def update_agent_model(req: UpdateAgentModel, request: Request):
    """Assign a provider/model to a specific agent."""
    await _auth(request)
    db = _db()

    if req.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail="Provider inconnu")

    current = await db.ai_agent_matrix.find_one({"_id": "matrix"})
    agents = current.get("agents", DEFAULT_AGENT_MATRIX) if current else {**DEFAULT_AGENT_MATRIX}
    agents[req.agent_id] = {"provider": req.provider, "model": req.model}

    await db.ai_agent_matrix.update_one(
        {"_id": "matrix"},
        {"$set": {"agents": agents, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"success": True, "agent": req.agent_id, "provider": req.provider, "model": req.model}


# Keep legacy endpoints working
@router.get("/config")
async def get_ai_config_legacy(request: Request):
    await _auth(request)
    return {"provider": "openrouter", "model_name": "llama-3.3-70b", "api_key_masked": "****"}


@router.post("/config")
async def save_ai_config_legacy(request: Request):
    return {"success": True, "message": "Use /providers/save-key instead"}


@router.post("/test")
async def test_ai_legacy(request: Request):
    return await test_provider(TestProviderRequest(provider="openrouter"), request)
