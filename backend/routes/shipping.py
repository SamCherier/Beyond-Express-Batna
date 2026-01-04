"""
Shipping Routes
API endpoints for carrier integration and order shipping
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Cookie
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import logging
from typing import List, Optional
from pydantic import BaseModel

from models import User, OrderStatus
from services.routing_engine import get_router, RoutingStrategy
from services.carriers.yalidine import YalidineCarrier

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Auth dependency
from auth_utils import verify_token

async def get_current_user(request: Request, session_token: Optional[str] = Cookie(None)) -> User:
    """Verify user authentication"""
    token = session_token
    
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
    
    user_id = payload.get("sub")
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)


# ===== REQUEST/RESPONSE MODELS =====

class ShipOrderRequest(BaseModel):
    order_id: str
    carrier_type: str = "yalidine"  # Default to Yalidine


class AutoShipRequest(BaseModel):
    order_id: str
    strategy: str = "priority"  # cheapest, fastest, priority, balanced


class BulkShipRequest(BaseModel):
    order_ids: List[str]
    carrier_type: str = "yalidine"


class ShipmentResult(BaseModel):
    order_id: str
    success: bool
    carrier_name: str = ""
    carrier_tracking_id: Optional[str] = None
    label_url: Optional[str] = None
    error_message: Optional[str] = None


# ===== ENDPOINTS =====

@router.get("/carrier-status/{carrier_type}")
async def get_carrier_status(
    carrier_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check if a carrier is configured and active for the current user
    Used by frontend to show/hide shipping buttons
    """
    try:
        config = await db.carrier_configs.find_one(
            {"user_id": current_user.id, "carrier_type": carrier_type},
            {"_id": 0, "credentials": 0}  # Don't return credentials
        )
        
        if not config:
            return {
                "carrier_type": carrier_type,
                "is_configured": False,
                "is_active": False,
                "test_mode": True,
                "can_ship": False,
                "message": "Transporteur non configuré"
            }
        
        return {
            "carrier_type": carrier_type,
            "carrier_name": config.get("carrier_name", carrier_type),
            "is_configured": True,
            "is_active": config.get("is_active", False),
            "test_mode": config.get("test_mode", True),
            "can_ship": config.get("is_active", False),
            "last_test_at": config.get("last_test_at"),
            "message": "Prêt à expédier" if config.get("is_active") else "Transporteur inactif"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting carrier status: {str(e)}")
        return {
            "carrier_type": carrier_type,
            "is_configured": False,
            "is_active": False,
            "can_ship": False,
            "message": str(e)
        }


@router.post("/ship", response_model=ShipmentResult)
async def ship_order(
    request: ShipOrderRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Ship a single order with a specific carrier
    
    This is the "Magic Button" - sends order to carrier and gets tracking
    """
    try:
        # Get order
        order = await db.orders.find_one(
            {"id": request.order_id, "user_id": current_user.id},
            {"_id": 0}
        )
        
        if not order:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        
        # Check if already shipped
        if order.get('carrier_tracking_id'):
            return ShipmentResult(
                order_id=request.order_id,
                success=True,
                carrier_name=order.get('carrier_type', ''),
                carrier_tracking_id=order.get('carrier_tracking_id'),
                error_message="Commande déjà expédiée"
            )
        
        # Get sender info from organization or user
        org = await db.organizations.find_one({}, {"_id": 0})
        if not org:
            org = {
                "name": "Beyond Express",
                "address": "City 84 centre-ville Batna",
                "phone": "+213 xxx xxx xxx"
            }
        
        order['sender'] = {
            "name": org.get('name', 'Beyond Express'),
            "phone": org.get('phone', ''),
            "address": org.get('address', 'Batna'),
            "wilaya": "Batna",
            "commune": "Batna"
        }
        
        # Use router to sync order
        smart_router = get_router()
        response = await smart_router.sync_order(
            order,
            request.carrier_type,
            current_user.id
        )
        
        return ShipmentResult(
            order_id=request.order_id,
            success=response.success,
            carrier_name=response.carrier_name,
            carrier_tracking_id=response.carrier_tracking_id,
            label_url=response.label_url,
            error_message=response.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error shipping order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-ship", response_model=ShipmentResult)
async def auto_ship_order(
    request: AutoShipRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Automatically select best carrier and ship order
    
    Uses Smart Router to analyze order and select optimal carrier
    """
    try:
        # Get order
        order = await db.orders.find_one(
            {"id": request.order_id, "user_id": current_user.id},
            {"_id": 0}
        )
        
        if not order:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        
        # Map strategy string to enum
        strategy_map = {
            "cheapest": RoutingStrategy.CHEAPEST,
            "fastest": RoutingStrategy.FASTEST,
            "priority": RoutingStrategy.PRIORITY,
            "balanced": RoutingStrategy.BALANCED
        }
        strategy = strategy_map.get(request.strategy, RoutingStrategy.PRIORITY)
        
        # Add sender info
        org = await db.organizations.find_one({}, {"_id": 0})
        order['sender'] = {
            "name": org.get('name', 'Beyond Express') if org else 'Beyond Express',
            "phone": org.get('phone', '') if org else '',
            "address": org.get('address', 'Batna') if org else 'Batna',
            "wilaya": "Batna",
            "commune": "Batna"
        }
        
        # Auto route and sync
        smart_router = get_router()
        response = await smart_router.auto_route_and_sync(
            order,
            current_user.id,
            strategy
        )
        
        return ShipmentResult(
            order_id=request.order_id,
            success=response.success,
            carrier_name=response.carrier_name,
            carrier_tracking_id=response.carrier_tracking_id,
            label_url=response.label_url,
            error_message=response.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error auto-shipping order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-ship")
async def bulk_ship_orders(
    request: BulkShipRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Ship multiple orders at once
    """
    try:
        results = []
        smart_router = get_router()
        
        # Get sender info once
        org = await db.organizations.find_one({}, {"_id": 0})
        sender = {
            "name": org.get('name', 'Beyond Express') if org else 'Beyond Express',
            "phone": org.get('phone', '') if org else '',
            "address": org.get('address', 'Batna') if org else 'Batna',
            "wilaya": "Batna",
            "commune": "Batna"
        }
        
        for order_id in request.order_ids:
            try:
                order = await db.orders.find_one(
                    {"id": order_id, "user_id": current_user.id},
                    {"_id": 0}
                )
                
                if not order:
                    results.append(ShipmentResult(
                        order_id=order_id,
                        success=False,
                        error_message="Commande non trouvée"
                    ))
                    continue
                
                order['sender'] = sender
                
                response = await smart_router.sync_order(
                    order,
                    request.carrier_type,
                    current_user.id
                )
                
                results.append(ShipmentResult(
                    order_id=order_id,
                    success=response.success,
                    carrier_name=response.carrier_name,
                    carrier_tracking_id=response.carrier_tracking_id,
                    label_url=response.label_url,
                    error_message=response.error_message
                ))
                
            except Exception as e:
                results.append(ShipmentResult(
                    order_id=order_id,
                    success=False,
                    error_message=str(e)
                ))
        
        success_count = sum(1 for r in results if r.success)
        
        return {
            "total": len(request.order_ids),
            "success": success_count,
            "failed": len(request.order_ids) - success_count,
            "results": [r.dict() for r in results]
        }
        
    except Exception as e:
        logger.error(f"❌ Error bulk shipping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/label/{order_id}")
async def get_shipping_label(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download shipping label PDF for an order
    """
    from fastapi.responses import Response
    
    try:
        # Get order
        order = await db.orders.find_one(
            {"id": order_id, "user_id": current_user.id},
            {"_id": 0}
        )
        
        if not order:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        
        carrier_type = order.get('carrier_type')
        carrier_tracking = order.get('carrier_tracking_id')
        
        if not carrier_type or not carrier_tracking:
            raise HTTPException(
                status_code=400,
                detail="Cette commande n'a pas encore été expédiée"
            )
        
        # Get carrier instance
        smart_router = get_router()
        carrier = await smart_router.get_carrier_instance(carrier_type, current_user.id)
        
        if not carrier:
            raise HTTPException(
                status_code=400,
                detail=f"Transporteur {carrier_type} non configuré"
            )
        
        # Download label
        label_pdf = await carrier.get_label(carrier_tracking)
        
        if not label_pdf:
            raise HTTPException(
                status_code=404,
                detail="Étiquette non disponible"
            )
        
        return Response(
            content=label_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="etiquette_{carrier_tracking}.pdf"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting label: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tracking/{order_id}")
async def get_carrier_tracking(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get tracking updates from carrier API
    """
    try:
        # Get order
        order = await db.orders.find_one(
            {"id": order_id, "user_id": current_user.id},
            {"_id": 0}
        )
        
        if not order:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        
        carrier_type = order.get('carrier_type')
        carrier_tracking = order.get('carrier_tracking_id')
        
        if not carrier_type or not carrier_tracking:
            return {
                "order_id": order_id,
                "carrier_synced": False,
                "updates": []
            }
        
        # Get carrier instance
        smart_router = get_router()
        carrier = await smart_router.get_carrier_instance(carrier_type, current_user.id)
        
        if not carrier:
            return {
                "order_id": order_id,
                "carrier_synced": True,
                "carrier_type": carrier_type,
                "carrier_tracking_id": carrier_tracking,
                "updates": [],
                "error": f"Transporteur {carrier_type} non configuré"
            }
        
        # Get tracking
        updates = await carrier.get_tracking(carrier_tracking)
        
        return {
            "order_id": order_id,
            "carrier_synced": True,
            "carrier_type": carrier_type,
            "carrier_tracking_id": carrier_tracking,
            "updates": [
                {
                    "status": u.status.value,
                    "timestamp": u.timestamp,
                    "location": u.location,
                    "description": u.description
                }
                for u in updates
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting tracking: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active-carriers")
async def get_user_active_carriers(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of active carriers for current user
    Used by frontend to show shipping options
    """
    try:
        configs = await db.carrier_configs.find(
            {"user_id": current_user.id, "is_active": True},
            {"_id": 0, "credentials": 0}  # Don't send credentials
        ).to_list(100)
        
        return {
            "carriers": [
                {
                    "carrier_type": c.get('carrier_type'),
                    "carrier_name": c.get('carrier_name'),
                    "test_mode": c.get('test_mode', True)
                }
                for c in configs
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting active carriers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
