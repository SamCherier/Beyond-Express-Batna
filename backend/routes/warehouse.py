from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== MODELS =====

class WarehouseZoneCreate(BaseModel):
    name: str
    zone_type: str  # cold, dry, fragile, standard
    capacity: int
    temperature: Optional[str] = None
    color: Optional[str] = "cyan"

class WarehouseZoneUpdate(BaseModel):
    used: Optional[int] = None
    capacity: Optional[int] = None
    temperature: Optional[str] = None

class DepotCreate(BaseModel):
    city: str
    wilaya: Optional[str] = None
    capacity_pct: int


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


# ===== SEED DEFAULT DATA =====

DEFAULT_ZONES = [
    {"id": "zone-a1", "name": "Zone Froide A1", "zone_type": "cold", "capacity": 100, "used": 68, "color": "cyan", "temperature": "4°C"},
    {"id": "zone-a2", "name": "Zone Sèche A2", "zone_type": "dry", "capacity": 200, "used": 170, "color": "green", "temperature": "20°C"},
    {"id": "zone-b1", "name": "Zone Fragile B1", "zone_type": "fragile", "capacity": 150, "used": 95, "color": "orange", "temperature": "18°C"},
    {"id": "zone-b2", "name": "Zone Standard B2", "zone_type": "standard", "capacity": 300, "used": 255, "color": "purple", "temperature": "22°C"},
]

DEFAULT_DEPOTS = [
    {"id": "depot-alger", "city": "Alger", "wilaya": "16", "capacity_pct": 85, "status": "warning"},
    {"id": "depot-oran", "city": "Oran", "wilaya": "31", "capacity_pct": 62, "status": "optimal"},
    {"id": "depot-constantine", "city": "Constantine", "wilaya": "25", "capacity_pct": 91, "status": "critical"},
    {"id": "depot-batna", "city": "Batna", "wilaya": "05", "capacity_pct": 45, "status": "optimal"},
]


async def ensure_seed():
    db = _db()
    count = await db.warehouse_zones.count_documents({})
    if count == 0:
        now = datetime.now(timezone.utc).isoformat()
        for z in DEFAULT_ZONES:
            await db.warehouse_zones.insert_one({**z, "created_at": now, "updated_at": now})
        for d in DEFAULT_DEPOTS:
            await db.warehouse_depots.insert_one({**d, "created_at": now, "updated_at": now})
        logger.info("Seeded warehouse data")


# ===== ROUTES =====

@router.get("/zones")
async def get_zones(request: Request):
    await _auth(request)
    db = _db()
    await ensure_seed()
    zones = await db.warehouse_zones.find({}, {"_id": 0}).to_list(100)
    for z in zones:
        for k in ["created_at", "updated_at"]:
            if k in z and isinstance(z[k], datetime):
                z[k] = z[k].isoformat()
    return zones


@router.patch("/zones/{zone_id}")
async def update_zone(zone_id: str, data: WarehouseZoneUpdate, request: Request):
    user = await _auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    db = _db()
    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.used is not None:
        update["used"] = data.used
    if data.capacity is not None:
        update["capacity"] = data.capacity
    if data.temperature is not None:
        update["temperature"] = data.temperature
    result = await db.warehouse_zones.update_one({"id": zone_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Zone not found")
    updated = await db.warehouse_zones.find_one({"id": zone_id}, {"_id": 0})
    return updated


@router.get("/depots")
async def get_depots(request: Request):
    await _auth(request)
    db = _db()
    await ensure_seed()
    depots = await db.warehouse_depots.find({}, {"_id": 0}).to_list(100)
    for d in depots:
        for k in ["created_at", "updated_at"]:
            if k in d and isinstance(d[k], datetime):
                d[k] = d[k].isoformat()
    return depots


@router.get("/stats")
async def get_warehouse_stats(request: Request):
    await _auth(request)
    db = _db()
    await ensure_seed()
    zones = await db.warehouse_zones.find({}, {"_id": 0}).to_list(100)
    total_cap = sum(z.get("capacity", 0) for z in zones)
    total_used = sum(z.get("used", 0) for z in zones)
    return {
        "total_capacity": total_cap,
        "total_used": total_used,
        "total_available": total_cap - total_used,
        "percentage": round((total_used / total_cap * 100), 1) if total_cap > 0 else 0,
        "zones_count": len(zones),
    }
