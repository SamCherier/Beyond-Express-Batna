"""WhatsApp Meta Cloud API Routes — Zero Cost Integration"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime, timezone

from services.whatsapp_meta import whatsapp_meta, DEFAULT_TEMPLATES, STATUS_TRIGGERS

logger = logging.getLogger(__name__)
router = APIRouter()


class ConfigureRequest(BaseModel):
    phone_id: str
    access_token: str
    enabled: bool = True
    triggers: Optional[dict] = None


class TestMessageRequest(BaseModel):
    to_phone: str
    template_name: str = "hello_world"


class SendTextRequest(BaseModel):
    to_phone: str
    message: str


@router.get("/status")
async def get_whatsapp_status():
    return whatsapp_meta.get_status()


@router.post("/configure")
async def configure_whatsapp(req: ConfigureRequest):
    whatsapp_meta.configure(
        phone_id=req.phone_id,
        access_token=req.access_token,
        enabled=req.enabled,
        triggers=req.triggers,
    )
    return {"success": True, "message": "Configuration WhatsApp sauvegardée"}


@router.post("/test")
async def send_test_message(req: TestMessageRequest):
    """Send a test template message (hello_world by default)."""
    result = await whatsapp_meta.send_template(
        to_phone=req.to_phone,
        template_name=req.template_name,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/send-text")
async def send_text_message(req: SendTextRequest):
    result = await whatsapp_meta.send_text(to_phone=req.to_phone, text=req.message)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/templates")
async def get_templates():
    return {"templates": list(DEFAULT_TEMPLATES.values())}


@router.get("/triggers")
async def get_triggers():
    return {"triggers": STATUS_TRIGGERS, "active": whatsapp_meta._triggers}


@router.get("/logs")
async def get_logs(request=None):
    """Get recent WhatsApp message logs from MongoDB."""
    try:
        from server import db
        logs = await db.whatsapp_logs.find(
            {}, {"_id": 0}
        ).sort("timestamp", -1).limit(50).to_list(50)
        return {"logs": logs}
    except Exception:
        return {"logs": []}
