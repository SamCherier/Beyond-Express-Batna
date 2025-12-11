"""
Driver API Routes
Endpoints for mobile driver app (Flutter)
Handles task management, status updates, and daily statistics
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from pydantic import BaseModel
import os
import logging

from models import User, OrderStatus, PaymentStatus

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Auth dependency
from fastapi import Request, Cookie
from auth_utils import verify_token

async def get_current_user(request: Request, session_token: Optional[str] = Cookie(None)) -> User:
    """Auth dependency - Only allows drivers"""
    token = session_token
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.sessions.find_one({"session_token": token}, {"_id": 0})
    if session_doc:
        if datetime.fromisoformat(session_doc['expires_at']) > datetime.now(timezone.utc):
            user_doc = await db.users.find_one({"id": session_doc['user_id']}, {"_id": 0})
            if user_doc:
                user = User(**user_doc)
                # Check if user is a driver
                if user.role != "delivery":
                    raise HTTPException(status_code=403, detail="Access denied. Drivers only.")
                return user
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    user = User(**user_doc)
    if user.role != "delivery":
        raise HTTPException(status_code=403, detail="Access denied. Drivers only.")
    
    return user

class StatusUpdate(BaseModel):
    order_id: str
    new_status: str  # "DELIVERED", "FAILED", "IN_TRANSIT", etc.
    failure_reason: Optional[str] = None
    notes: Optional[str] = None
    location: Optional[str] = None

@router.get("/tasks")
async def get_driver_tasks(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of orders assigned to the driver
    Returns only orders that are "In Transit" or "Picked Up"
    
    Response includes:
    - Client name, phone (clickable), address
    - COD amount
    - Map coordinates (if available)
    - Order status and payment status
    """
    try:
        # Query orders assigned to this driver
        # Statuses: IN_TRANSIT, PICKED_UP (ready for delivery)
        query = {
            "delivery_partner": current_user.id,
            "status": {
                "$in": ["IN_TRANSIT", "PICKED_UP", "OUT_FOR_DELIVERY"]
            }
        }
        
        orders = await db.orders.find(query, {"_id": 0}).sort("created_at", 1).to_list(1000)
        
        # Format response for mobile app
        tasks = []
        for order in orders:
            recipient = order.get('recipient', {})
            
            task = {
                "order_id": order.get('id'),
                "tracking_id": order.get('tracking_id'),
                "status": order.get('status'),
                "payment_status": order.get('payment_status', 'unpaid'),
                "client": {
                    "name": recipient.get('name', 'N/A'),
                    "phone": recipient.get('phone', 'N/A'),
                    "address": recipient.get('address', 'N/A'),
                    "wilaya": recipient.get('wilaya', 'N/A'),
                    "commune": recipient.get('commune', 'N/A')
                },
                "cod_amount": order.get('cod_amount', 0),
                "shipping_cost": order.get('shipping_cost', 0),
                "net_to_merchant": order.get('net_to_merchant', 0),
                "description": order.get('description', ''),
                "pin_code": order.get('pin_code', ''),
                "created_at": order.get('created_at'),
                # Map coordinates (future feature)
                "coordinates": {
                    "lat": None,
                    "lng": None
                }
            }
            tasks.append(task)
        
        logger.info(f"✅ Driver {current_user.id} retrieved {len(tasks)} tasks")
        
        return {
            "tasks": tasks,
            "count": len(tasks),
            "driver_id": current_user.id,
            "driver_name": current_user.name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting driver tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-status")
async def update_order_status(
    status_update: StatusUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update order status from driver
    
    CRITICAL FINANCIAL LOGIC:
    - If status = "DELIVERED" → Automatically set payment_status to "COLLECTED_BY_DRIVER"
    - If status = "FAILED" → Require failure_reason
    
    Allowed statuses:
    - DELIVERED: Successfully delivered to customer
    - FAILED: Failed delivery (requires reason)
    - IN_TRANSIT: Currently in transit
    - OUT_FOR_DELIVERY: Out for delivery
    """
    try:
        # Find order
        order = await db.orders.find_one(
            {
                "id": status_update.order_id,
                "delivery_partner": current_user.id
            },
            {"_id": 0}
        )
        
        if not order:
            raise HTTPException(
                status_code=404, 
                detail="Order not found or not assigned to this driver"
            )
        
        # Validate status
        valid_statuses = ["DELIVERED", "FAILED", "IN_TRANSIT", "OUT_FOR_DELIVERY", "RETURNED"]
        if status_update.new_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # If FAILED, require failure reason
        if status_update.new_status == "FAILED" and not status_update.failure_reason:
            raise HTTPException(
                status_code=400,
                detail="Failure reason is required when marking order as FAILED"
            )
        
        # Prepare update data
        update_data = {
            "status": status_update.new_status,
            "updated_at": datetime.now(timezone.utc)
        }
        
        # CRITICAL FINANCIAL LOGIC: Auto-update payment status when DELIVERED
        if status_update.new_status == "DELIVERED":
            update_data["payment_status"] = "collected_by_driver"
            update_data["collected_date"] = datetime.now(timezone.utc)
            logger.info(f"💰 Order {status_update.order_id} DELIVERED → payment_status = COLLECTED_BY_DRIVER")
        
        # If FAILED, store failure reason
        if status_update.new_status == "FAILED":
            update_data["failure_reason"] = status_update.failure_reason
            update_data["failed_date"] = datetime.now(timezone.utc)
        
        # Store notes and location if provided
        if status_update.notes:
            update_data["driver_notes"] = status_update.notes
        
        if status_update.location:
            update_data["delivery_location"] = status_update.location
        
        # Update order
        result = await db.orders.update_one(
            {"id": status_update.order_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update order")
        
        logger.info(f"✅ Driver {current_user.id} updated order {status_update.order_id} → {status_update.new_status}")
        
        return {
            "success": True,
            "order_id": status_update.order_id,
            "new_status": status_update.new_status,
            "payment_status": update_data.get("payment_status", order.get("payment_status")),
            "message": f"Order status updated to {status_update.new_status}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_driver_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get driver's daily statistics
    
    Returns:
    - Total cash collected today (COD amounts for delivered orders)
    - Number of deliveries today
    - Number of failed deliveries today
    - Pending deliveries
    """
    try:
        # Get today's date range (00:00 to 23:59)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Query delivered orders today
        delivered_today = await db.orders.find({
            "delivery_partner": current_user.id,
            "status": "DELIVERED",
            "updated_at": {
                "$gte": today_start.isoformat(),
                "$lt": today_end.isoformat()
            }
        }, {"_id": 0}).to_list(1000)
        
        # Calculate total cash collected
        total_cash = sum(order.get('cod_amount', 0) for order in delivered_today)
        delivery_count = len(delivered_today)
        
        # Query failed orders today
        failed_today = await db.orders.count_documents({
            "delivery_partner": current_user.id,
            "status": "FAILED",
            "updated_at": {
                "$gte": today_start.isoformat(),
                "$lt": today_end.isoformat()
            }
        })
        
        # Query pending deliveries (IN_TRANSIT, OUT_FOR_DELIVERY, PICKED_UP)
        pending = await db.orders.count_documents({
            "delivery_partner": current_user.id,
            "status": {
                "$in": ["IN_TRANSIT", "OUT_FOR_DELIVERY", "PICKED_UP"]
            }
        })
        
        # Query total collected but not yet transferred
        all_collected = await db.orders.find({
            "delivery_partner": current_user.id,
            "payment_status": "collected_by_driver"
        }, {"_id": 0}).to_list(1000)
        
        total_pending_transfer = sum(order.get('cod_amount', 0) for order in all_collected)
        
        logger.info(f"✅ Driver {current_user.id} stats: {delivery_count} deliveries, {total_cash} DZD collected today")
        
        return {
            "driver_id": current_user.id,
            "driver_name": current_user.name,
            "today": {
                "deliveries": delivery_count,
                "failed": failed_today,
                "total_cash_collected": round(total_cash, 2),
                "date": today_start.isoformat()
            },
            "pending": {
                "pending_deliveries": pending,
                "total_cash_to_transfer": round(total_pending_transfer, 2)
            },
            "message": f"Vous devez verser {round(total_cash, 2)} DZD aujourd'hui"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting driver stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
