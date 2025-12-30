"""
Webhook Routes
Endpoints for receiving carrier webhook notifications
"""
from fastapi import APIRouter, HTTPException, Request, Header, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import logging
import hmac
import hashlib
from typing import Optional

from models import OrderStatus, PaymentStatus
from services.carriers.base import ShipmentStatus

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Status mapping from carrier to internal
YALIDINE_STATUS_MAP = {
    "En préparation": OrderStatus.PREPARING,
    "Prêt à expédier": OrderStatus.READY_TO_SHIP,
    "Expédié vers le centre": OrderStatus.IN_TRANSIT,
    "Reçu au centre": OrderStatus.IN_TRANSIT,
    "En cours de livraison": OrderStatus.IN_TRANSIT,
    "En attente du client": OrderStatus.IN_TRANSIT,
    "Livré": OrderStatus.DELIVERED,
    "Echec livraison": OrderStatus.FAILED,
    "Retour en cours": OrderStatus.RETURNED,
    "Retourné": OrderStatus.RETURNED,
    "Annulé": OrderStatus.ARCHIVED,
}


async def process_status_update(
    order_id: str,
    carrier_type: str,
    carrier_status: str,
    carrier_tracking: str,
    location: Optional[str] = None,
    notes: Optional[str] = None
):
    """
    Process status update from carrier webhook
    Updates order status and adds tracking event
    """
    try:
        # Find order by carrier tracking ID
        order = await db.orders.find_one(
            {"carrier_tracking_id": carrier_tracking},
            {"_id": 0}
        )
        
        if not order:
            # Try finding by our tracking ID
            order = await db.orders.find_one(
                {"tracking_id": order_id},
                {"_id": 0}
            )
        
        if not order:
            logger.warning(f"⚠️ Order not found for webhook: {carrier_tracking}")
            return
        
        # Map carrier status to internal status
        if carrier_type == "yalidine":
            new_status = YALIDINE_STATUS_MAP.get(carrier_status, OrderStatus.IN_TRANSIT)
        else:
            new_status = OrderStatus.IN_TRANSIT
        
        # Update order
        update_data = {
            "status": new_status.value,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Handle DELIVERED status - update payment
        if new_status == OrderStatus.DELIVERED:
            update_data["payment_status"] = PaymentStatus.COLLECTED_BY_DRIVER.value
            update_data["collected_date"] = datetime.now(timezone.utc).isoformat()
            logger.info(f"💰 Order {order['id']} delivered - payment collected")
        
        # Handle RETURNED status
        if new_status == OrderStatus.RETURNED:
            update_data["payment_status"] = PaymentStatus.RETURNED.value
            logger.info(f"↩️ Order {order['id']} returned")
        
        await db.orders.update_one(
            {"id": order['id']},
            {"$set": update_data}
        )
        
        # Add tracking event
        import uuid
        tracking_event = {
            "id": str(uuid.uuid4()),
            "order_id": order['id'],
            "status": carrier_status,
            "location": location,
            "notes": f"[{carrier_type.upper()}] {notes or carrier_status}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db.tracking_events.insert_one(tracking_event)
        
        logger.info(f"✅ Webhook processed: {order['id']} -> {new_status.value}")
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}")


@router.post("/yalidine")
async def yalidine_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_signature: Optional[str] = Header(None)
):
    """
    Receive webhook notifications from Yalidine
    
    Yalidine sends status updates when:
    - Parcel is picked up
    - Parcel arrives at center
    - Parcel is out for delivery
    - Parcel is delivered
    - Delivery failed
    - Parcel returned
    
    Expected payload:
    {
        "tracking": "YAL-123456",
        "order_id": "BEX-XXXX",
        "status": "Livré",
        "center": "Alger Centre",
        "updated_at": "2025-01-15T10:30:00Z"
    }
    """
    try:
        body = await request.body()
        data = await request.json()
        
        logger.info(f"📨 Yalidine webhook received: {data}")
        
        # TODO: Verify webhook signature if Yalidine provides one
        # For now, we'll accept all webhooks
        
        tracking = data.get('tracking', '')
        order_id = data.get('order_id', '')
        status = data.get('status', '')
        center = data.get('center', '')
        
        if not tracking and not order_id:
            raise HTTPException(status_code=400, detail="Missing tracking or order_id")
        
        # Process in background
        background_tasks.add_task(
            process_status_update,
            order_id=order_id,
            carrier_type="yalidine",
            carrier_status=status,
            carrier_tracking=tracking,
            location=center,
            notes=data.get('notes')
        )
        
        return {"status": "received", "tracking": tracking}
        
    except Exception as e:
        logger.error(f"❌ Yalidine webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dhd")
async def dhd_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Receive webhook notifications from DHD Express
    """
    try:
        data = await request.json()
        logger.info(f"📨 DHD webhook received: {data}")
        
        # DHD-specific payload parsing
        tracking = data.get('shipment_id', '') or data.get('tracking', '')
        status = data.get('status', '')
        
        background_tasks.add_task(
            process_status_update,
            order_id=data.get('reference', ''),
            carrier_type="dhd",
            carrier_status=status,
            carrier_tracking=tracking,
            location=data.get('location'),
            notes=data.get('message')
        )
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"❌ DHD webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/zr-express")
async def zr_express_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Receive webhook notifications from ZR Express
    """
    try:
        data = await request.json()
        logger.info(f"📨 ZR Express webhook received: {data}")
        
        background_tasks.add_task(
            process_status_update,
            order_id=data.get('order_ref', ''),
            carrier_type="zr_express",
            carrier_status=data.get('status', ''),
            carrier_tracking=data.get('tracking_number', ''),
            location=data.get('current_location'),
            notes=data.get('status_message')
        )
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"❌ ZR Express webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_webhook_endpoint():
    """
    Test endpoint to verify webhook URLs are accessible
    """
    return {
        "status": "ok",
        "message": "Webhook endpoint is active",
        "endpoints": [
            "/api/webhooks/yalidine",
            "/api/webhooks/dhd",
            "/api/webhooks/zr-express"
        ]
    }
