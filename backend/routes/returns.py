from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ===== MODELS =====

class ReturnReason(str, Enum):
    DAMAGED = "damaged"
    ABSENT = "absent"
    WRONG_ITEM = "wrong_item"
    CUSTOMER_REQUEST = "customer_request"
    REFUSED_PRICE = "refused_price"
    WRONG_ADDRESS = "wrong_address"

class ReturnStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RESTOCKED = "restocked"
    DISCARDED = "discarded"

class ReturnCreate(BaseModel):
    order_id: Optional[str] = ""
    tracking_id: str
    customer_name: str
    wilaya: str
    reason: ReturnReason
    notes: Optional[str] = None

class ReturnUpdate(BaseModel):
    status: Optional[ReturnStatus] = None
    notes: Optional[str] = None

# ===== BUSINESS LOGIC =====

RESTOCK_REASONS = {ReturnReason.ABSENT, ReturnReason.CUSTOMER_REQUEST, ReturnReason.REFUSED_PRICE, ReturnReason.WRONG_ADDRESS}
DISCARD_REASONS = {ReturnReason.DAMAGED}

def decide_return_action(reason: ReturnReason) -> dict:
    if reason in RESTOCK_REASONS:
        return {"decision": "restock", "label": "Remise en Stock", "icon": "archive"}
    elif reason in DISCARD_REASONS:
        return {"decision": "discard", "label": "Mise au Rebut", "icon": "trash"}
    else:
        return {"decision": "inspect", "label": "Controle Qualite", "icon": "clipboard"}

# Auth helper - extracts user from request directly
async def _auth(request: Request):
    from server import db, verify_token
    from models import User
    # Try cookie
    token = request.cookies.get("session_token")
    # Fallback to Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Try session token
    session_doc = await db.sessions.find_one({"session_token": token}, {"_id": 0})
    if session_doc:
        if datetime.fromisoformat(session_doc['expires_at']) > datetime.now(timezone.utc):
            user_doc = await db.users.find_one({"id": session_doc['user_id']}, {"_id": 0})
            if user_doc:
                return User(**user_doc)
    # Try JWT
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_doc = await db.users.find_one({"id": payload.get("sub")}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user_doc)

def _db():
    from server import db
    return db

# ===== ROUTES =====

@router.get("")
async def get_returns(request: Request):
    db = _db()
    user = await _auth(request)

    query = {} if user.role == "admin" else {"user_id": user.id}
    returns_list = await db.returns.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)

    for r in returns_list:
        for k in ["created_at", "updated_at"]:
            if k in r and isinstance(r[k], datetime):
                r[k] = r[k].isoformat()
    return returns_list


@router.get("/stats")
async def get_returns_stats(request: Request):
    db = _db()
    user = await _auth(request)

    match_stage = {} if user.role == "admin" else {"user_id": user.id}

    total = await db.returns.count_documents(match_stage)
    restocked = await db.returns.count_documents({**match_stage, "status": ReturnStatus.RESTOCKED})
    discarded = await db.returns.count_documents({**match_stage, "status": ReturnStatus.DISCARDED})
    pending = await db.returns.count_documents({**match_stage, "status": ReturnStatus.PENDING})
    approved = await db.returns.count_documents({**match_stage, "status": ReturnStatus.APPROVED})

    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})
    pipeline.extend([
        {"$group": {"_id": "$reason", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ])
    reason_breakdown = []
    async for doc in db.returns.aggregate(pipeline):
        reason_breakdown.append({"reason": doc["_id"], "count": doc["count"]})

    return {
        "total": total,
        "restocked": restocked,
        "discarded": discarded,
        "pending": pending,
        "approved": approved,
        "reason_breakdown": reason_breakdown
    }


@router.post("")
async def create_return(data: ReturnCreate, request: Request):
    db = _db()
    from server import audit_logger
    from audit_logger import AuditAction
    user = await _auth(request)

    action = decide_return_action(data.reason)

    return_doc = {
        "id": str(uuid.uuid4()),
        "order_id": data.order_id or "",
        "tracking_id": data.tracking_id,
        "customer_name": data.customer_name,
        "wilaya": data.wilaya,
        "reason": data.reason.value,
        "status": ReturnStatus.PENDING.value,
        "decision": action["decision"],
        "decision_label": action["label"],
        "decision_icon": action["icon"],
        "stock_impact": data.reason in RESTOCK_REASONS,
        "notes": data.notes,
        "user_id": user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    await db.returns.insert_one(return_doc)

    # Update linked order if exists
    if data.order_id:
        await db.orders.update_one(
            {"id": data.order_id},
            {"$set": {"status": "returned", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )

    await audit_logger.log_action(
        action=AuditAction.STATUS_CHANGE,
        user_id=user.id,
        user_email=user.email,
        details={"return_id": return_doc["id"], "reason": data.reason.value, "decision": action["decision"]},
        ip_address=request.client.host if request.client else None,
        status="success"
    )

    return_doc.pop("_id", None)
    return return_doc


@router.patch("/{return_id}")
async def update_return(return_id: str, data: ReturnUpdate, request: Request):
    db = _db()
    user = await _auth(request)

    ret = await db.returns.find_one({"id": return_id}, {"_id": 0})
    if not ret:
        raise HTTPException(status_code=404, detail="Return not found")

    update_dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.status:
        update_dict["status"] = data.status.value
    if data.notes is not None:
        update_dict["notes"] = data.notes

    await db.returns.update_one({"id": return_id}, {"$set": update_dict})

    updated = await db.returns.find_one({"id": return_id}, {"_id": 0})
    for k in ["created_at", "updated_at"]:
        if k in updated and isinstance(updated[k], datetime):
            updated[k] = updated[k].isoformat()
    return updated


@router.delete("/{return_id}")
async def delete_return(return_id: str, request: Request):
    db = _db()
    user = await _auth(request)

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    result = await db.returns.delete_one({"id": return_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Return not found")

    return {"message": "Return deleted"}
