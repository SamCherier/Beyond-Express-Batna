"""
Proforma Invoice / Décharge de Colis API
Generates invoice data for a batch of orders.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


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
    from server import db, get_current_user
    current_user = await get_current_user(request)

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
    # Remove _id from counter response if leaked
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
