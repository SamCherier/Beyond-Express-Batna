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
    carrier_type: str = "auto"  # "auto" = Smart Router, or specific carrier
    use_smart_routing: bool = True  # Enable AI routing


class ShipmentResult(BaseModel):
    order_id: str
    success: bool
    carrier_name: str = ""
    carrier_tracking_id: Optional[str] = None
    label_url: Optional[str] = None
    error_message: Optional[str] = None
    routing_reason: Optional[str] = None  # Why this carrier was chosen


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
                
                # Skip if already shipped
                if order.get('carrier_tracking_id'):
                    results.append(ShipmentResult(
                        order_id=order_id,
                        success=True,
                        carrier_name=order.get('carrier_type', ''),
                        carrier_tracking_id=order.get('carrier_tracking_id'),
                        error_message="Déjà expédié",
                        routing_reason="Commande déjà expédiée - Skip"
                    ))
                    continue
                
                order['sender'] = sender
                
                # Use Smart Routing if enabled
                if request.use_smart_routing or request.carrier_type == "auto":
                    # 🧠 AI-Powered Routing
                    response, recommendation = await smart_router.smart_ship(
                        order,
                        current_user.id
                    )
                    routing_reason = recommendation.reason
                else:
                    # Manual carrier selection
                    response = await smart_router.sync_order(
                        order,
                        request.carrier_type,
                        current_user.id
                    )
                    routing_reason = f"Sélection manuelle: {request.carrier_type}"
                
                results.append(ShipmentResult(
                    order_id=order_id,
                    success=response.success,
                    carrier_name=response.carrier_name,
                    carrier_tracking_id=response.carrier_tracking_id,
                    label_url=response.label_url,
                    error_message=response.error_message,
                    routing_reason=routing_reason
                ))
                
            except Exception as e:
                results.append(ShipmentResult(
                    order_id=order_id,
                    success=False,
                    error_message=str(e)
                ))
        
        success_count = sum(1 for r in results if r.success)
        
        # Group results by carrier for summary
        carrier_summary = {}
        for r in results:
            if r.success and r.carrier_name:
                carrier_summary[r.carrier_name] = carrier_summary.get(r.carrier_name, 0) + 1
        
        return {
            "total": len(request.order_ids),
            "success": success_count,
            "failed": len(request.order_ids) - success_count,
            "smart_routing": request.use_smart_routing,
            "carrier_summary": carrier_summary,
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
    Uses unified label generator with carrier-specific handling
    """
    from fastapi.responses import Response
    from services.label_engine import get_label_generator
    
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
        
        # Get label generator
        label_gen = get_label_generator()
        
        # Try to get official label from carrier first
        if carrier_type and carrier_tracking:
            smart_router = get_router()
            carrier = await smart_router.get_carrier_instance(carrier_type, current_user.id)
            
            if carrier:
                try:
                    official_label = await carrier.get_label(carrier_tracking)
                    if official_label:
                        return Response(
                            content=official_label,
                            media_type="application/pdf",
                            headers={
                                "Content-Disposition": f'attachment; filename="etiquette_{carrier_tracking}.pdf"'
                            }
                        )
                except Exception as e:
                    logger.warning(f"Could not fetch official label: {e}")
        
        # Fallback: Generate unified label
        label_pdf = label_gen.generate_single_label(order)
        tracking_id = carrier_tracking or order.get('tracking_id', 'label')
        
        return Response(
            content=label_pdf.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="etiquette_{tracking_id}.pdf"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting label: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class BulkLabelRequest(BaseModel):
    order_ids: List[str]


@router.post("/bulk-labels")
async def generate_bulk_labels(
    request: BulkLabelRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate bulk labels PDF for multiple orders
    
    Creates a single PDF with all labels merged (A6 format)
    Perfect for thermal printers and batch printing
    """
    from fastapi.responses import Response
    from services.label_engine import get_label_generator
    
    try:
        if not request.order_ids:
            raise HTTPException(status_code=400, detail="Aucune commande sélectionnée")
        
        # Fetch all orders
        orders = await db.orders.find(
            {
                "id": {"$in": request.order_ids},
                "user_id": current_user.id
            },
            {"_id": 0}
        ).to_list(500)
        
        if not orders:
            raise HTTPException(status_code=404, detail="Aucune commande trouvée")
        
        logger.info(f"📄 Generating bulk labels for {len(orders)} orders")
        
        # Generate merged PDF
        label_gen = get_label_generator()
        merged_pdf = label_gen.generate_bulk_labels(orders)
        
        # Generate filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"etiquettes_x{len(orders)}_{timestamp}.pdf"
        
        return Response(
            content=merged_pdf.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Label-Count": str(len(orders))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating bulk labels: {str(e)}")
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



# =====================================
# UNIFIED TRACKING SYSTEM - Control Tower
# =====================================

class SyncStatusRequest(BaseModel):
    force_advance: bool = False  # For ZR Express Mock - Time Travel


class BulkSyncRequest(BaseModel):
    order_ids: List[str]
    force_advance: bool = False


@router.post("/sync-status/{order_id}")
async def sync_order_status(
    order_id: str,
    request: SyncStatusRequest = None,
    current_user: User = Depends(get_current_user)
):
    """
    🔄 Sync tracking status for a single order from its carrier
    
    For ZR Express (Mock): Uses "Time Travel" simulation
    - 1st click: PENDING -> IN_TRANSIT
    - 2nd click: IN_TRANSIT -> DELIVERED
    
    For Real Carriers (Yalidine): Fetches actual status from API
    """
    from services.tracking_service import TrackingService
    
    try:
        # Verify order belongs to user
        order = await db.orders.find_one(
            {"id": order_id, "user_id": current_user.id},
            {"_id": 0}
        )
        
        if not order:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        
        # Initialize tracking service
        tracking_svc = TrackingService()
        
        # Sync status (force_advance for ZR Mock time travel)
        force = request.force_advance if request else False
        result = await tracking_svc.sync_order_status(
            order_id=order_id,
            user_id=current_user.id,
            force_advance=force
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error syncing status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-sync-status")
async def bulk_sync_status(
    request: BulkSyncRequest,
    current_user: User = Depends(get_current_user)
):
    """
    🔄 Sync tracking status for multiple orders at once
    
    Perfect for "Actualiser Tout" button in dashboard
    """
    from services.tracking_service import TrackingService
    
    try:
        if not request.order_ids:
            raise HTTPException(status_code=400, detail="Aucune commande sélectionnée")
        
        tracking_svc = TrackingService()
        results = []
        
        for order_id in request.order_ids:
            try:
                # Verify order belongs to user
                order = await db.orders.find_one(
                    {"id": order_id, "user_id": current_user.id},
                    {"_id": 0}
                )
                
                if not order:
                    results.append({
                        "order_id": order_id,
                        "success": False,
                        "error": "Commande non trouvée"
                    })
                    continue
                
                result = await tracking_svc.sync_order_status(
                    order_id=order_id,
                    user_id=current_user.id,
                    force_advance=request.force_advance
                )
                results.append(result)
                
            except Exception as e:
                results.append({
                    "order_id": order_id,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        success_count = sum(1 for r in results if r.get('success'))
        changed_count = sum(1 for r in results if r.get('status_changed'))
        
        return {
            "total": len(request.order_ids),
            "success": success_count,
            "failed": len(request.order_ids) - success_count,
            "status_changed": changed_count,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error bulk syncing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline/{order_id}")
async def get_order_timeline(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    📊 Get full tracking timeline for an order
    
    Returns all tracking events with status metadata for visual display
    """
    from services.status_mapper import MasterStatus, get_status_meta
    
    try:
        # Verify order belongs to user
        order = await db.orders.find_one(
            {"id": order_id, "user_id": current_user.id},
            {"_id": 0}
        )
        
        if not order:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        
        # Get tracking events
        events = await db.tracking_events.find(
            {"order_id": order_id},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(100)  # Oldest first for timeline
        
        # Current status
        current_status = order.get('status', 'pending')
        
        # Define timeline steps
        timeline_steps = [
            {"status": "pending", "label": "En attente", "icon": "⏳"},
            {"status": "preparing", "label": "Préparation", "icon": "📦"},
            {"status": "ready_to_ship", "label": "Prêt", "icon": "✅"},
            {"status": "picked_up", "label": "Récupéré", "icon": "🚛"},
            {"status": "in_transit", "label": "En transit", "icon": "🚚"},
            {"status": "out_for_delivery", "label": "En livraison", "icon": "🏃"},
            {"status": "delivered", "label": "Livré", "icon": "✅"},
        ]
        
        # Find current step index
        status_order = [s["status"] for s in timeline_steps]
        current_index = -1
        
        if current_status in status_order:
            current_index = status_order.index(current_status)
        elif current_status in ["returned", "failed", "cancelled"]:
            # Terminal states - show at end
            current_index = len(timeline_steps)
        
        # Build timeline with completion status
        timeline = []
        for i, step in enumerate(timeline_steps):
            step_data = {
                **step,
                "completed": i < current_index,
                "current": i == current_index,
                "upcoming": i > current_index,
                "timestamp": None
            }
            
            # Find matching event
            for event in events:
                if event.get('status') == step["status"]:
                    step_data["timestamp"] = event.get('timestamp')
                    step_data["location"] = event.get('location')
                    break
            
            timeline.append(step_data)
        
        # Handle terminal states
        terminal_status = None
        if current_status == "returned":
            terminal_status = {
                "status": "returned",
                "label": "Retourné",
                "icon": "↩️",
                "color": "#EF4444",
                "current": True
            }
        elif current_status == "failed":
            terminal_status = {
                "status": "failed",
                "label": "Échec",
                "icon": "⚠️",
                "color": "#F97316",
                "current": True
            }
        elif current_status == "cancelled":
            terminal_status = {
                "status": "cancelled",
                "label": "Annulé",
                "icon": "❌",
                "color": "#6B7280",
                "current": True
            }
        
        return {
            "order_id": order_id,
            "tracking_id": order.get('tracking_id'),
            "carrier_type": order.get('carrier_type'),
            "carrier_tracking_id": order.get('carrier_tracking_id'),
            "current_status": current_status,
            "last_sync_at": order.get('last_sync_at'),
            "timeline": timeline,
            "terminal_status": terminal_status,
            "events": events
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
