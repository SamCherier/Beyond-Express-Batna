"""
Proforma Invoice / Décharge de Colis API
Generates invoice data for a batch of orders.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import logging

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

    # Try session token
    session = await db.sessions.find_one({"session_token": token}, {"_id": 0})
    if session:
        from datetime import datetime as dt
        if dt.fromisoformat(session["expires_at"]) > datetime.now(timezone.utc):
            user_doc = await db.users.find_one({"id": session["user_id"]}, {"_id": 0})
            if user_doc:
                return User(**user_doc)

    # Try JWT token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user_doc)


class ProformaRequest(BaseModel):
    order_ids: List[str]
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    client_address: Optional[str] = None
    lieu: str = "Batna"


@router.post("/generate")
async def generate_proforma(req: ProformaRequest, request: Request):
    """Generate a proforma invoice for a set of orders."""
    db = _db()
    current_user = await _auth(request)

    if not req.order_ids:
        raise HTTPException(status_code=400, detail="Aucune commande sélectionnée")

    orders = await db.orders.find(
        {"id": {"$in": req.order_ids}},
        {"_id": 0}
    ).to_list(length=500)

    if not orders:
        raise HTTPException(status_code=404, detail="Aucune commande trouvée")

    seq = await db.counters.find_one_and_update(
        {"_id": "proforma_seq"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq_num = seq.get("seq", 1) if seq else 1
    reference = f"BEY-{seq_num:04d}"

    now = datetime.now(timezone.utc)

    total_montant = 0
    total_livraison = 0
    total_prestation = 0
    total_net = 0

    items = []
    for o in orders:
        recipient = o.get("recipient", {})
        cod = float(o.get("cod_amount", 0))
        shipping = float(o.get("shipping_cost", 0))
        prestation = round(shipping * 0.15, 2)
        net = round(cod - shipping - prestation, 2)

        total_montant += cod
        total_livraison += shipping
        total_prestation += prestation
        total_net += net

        items.append({
            "reference": o.get("tracking_id", ""),
            "article": o.get("description", "Colis"),
            "destinataire": recipient.get("name", ""),
            "telephone": recipient.get("phone", ""),
            "wilaya": recipient.get("wilaya", ""),
            "commune": recipient.get("commune", ""),
            "poids": o.get("weight", "1.0"),
            "montant": cod,
            "tarif_livraison": shipping,
            "tarif_prestation": prestation,
            "net": net,
        })

    client_name = req.client_name
    if not client_name and orders:
        first = orders[0]
        client_name = first.get("sender", {}).get("name", current_user.name)

    invoice = {
        "id": str(uuid.uuid4()),
        "reference": reference,
        "date": now.strftime("%d / %m / %Y"),
        "lieu": req.lieu,
        "client": {
            "name": client_name or current_user.name,
            "phone": req.client_phone or current_user.phone_number or "",
            "email": req.client_email or current_user.email,
            "address": req.client_address or "",
        },
        "items": items,
        "totals": {
            "montant": round(total_montant, 2),
            "livraison": round(total_livraison, 2),
            "prestation": round(total_prestation, 2),
            "net": round(total_net, 2),
        },
        "order_count": len(items),
        "created_by": current_user.id,
        "created_at": now.isoformat(),
    }

    await db.proforma_invoices.insert_one({**invoice, "_id": invoice["id"]})

    return invoice
