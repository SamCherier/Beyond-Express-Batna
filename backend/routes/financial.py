"""
Financial Management & COD Reconciliation Routes
Handles payment status tracking and batch transfers
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from typing import List, Dict, Any
import os
import logging

from models import Order, User, PaymentStatus, BatchPaymentUpdate

logger = logging.getLogger(__name__)
router = APIRouter()

# Auth dependency placeholder - will be injected from server.py
async def get_current_user_dependency():
    raise HTTPException(status_code=500, detail="Auth dependency not configured")

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

@router.patch("/{order_id}/payment-status")
async def update_payment_status(
    order_id: str,
    new_status: PaymentStatus,
    notes: str = None,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Update payment status for a single order (Admin only)
    """
    try:
        # Only admins can update payment status
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can update payment status")
        
        # Find order
        order = await db.orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Prepare update
        update_data = {
            "payment_status": new_status.value,
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Add timestamp based on status
        if new_status == PaymentStatus.COLLECTED_BY_DRIVER:
            update_data["collected_date"] = datetime.now(timezone.utc)
        elif new_status == PaymentStatus.TRANSFERRED_TO_MERCHANT:
            update_data["transferred_date"] = datetime.now(timezone.utc)
        
        # Update order
        await db.orders.update_one(
            {"id": order_id},
            {"$set": update_data}
        )
        
        logger.info(f"✅ Payment status updated for order {order_id}: {new_status.value}")
        
        return {
            "success": True,
            "order_id": order_id,
            "new_status": new_status.value,
            "message": f"Payment status updated to {new_status.value}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating payment status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-update-payment")
async def batch_update_payment_status(
    batch_update: BatchPaymentUpdate,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Batch update payment status for multiple orders (CRITICAL for weekly transfers)
    Example: Select 50 orders with status "COLLECTED_BY_DRIVER" and mark as "TRANSFERRED_TO_MERCHANT"
    """
    try:
        # Only admins can batch update
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can batch update payment status")
        
        if not batch_update.order_ids:
            raise HTTPException(status_code=400, detail="No order IDs provided")
        
        # Prepare update
        update_data = {
            "payment_status": batch_update.new_status.value,
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Add timestamp based on status
        if batch_update.new_status == PaymentStatus.COLLECTED_BY_DRIVER:
            update_data["collected_date"] = datetime.now(timezone.utc)
        elif batch_update.new_status == PaymentStatus.TRANSFERRED_TO_MERCHANT:
            update_data["transferred_date"] = datetime.now(timezone.utc)
        
        # Batch update
        result = await db.orders.update_many(
            {"id": {"$in": batch_update.order_ids}},
            {"$set": update_data}
        )
        
        logger.info(f"✅ Batch payment status update: {result.modified_count} orders updated to {batch_update.new_status.value}")
        
        return {
            "success": True,
            "updated_count": result.modified_count,
            "new_status": batch_update.new_status.value,
            "message": f"{result.modified_count} orders updated to {batch_update.new_status.value}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/financial-summary")
async def get_financial_summary(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Financial summary dashboard (Admin only)
    Shows: Total COD collected, pending, transferred, etc.
    """
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Aggregate by payment status
        pipeline = [
            {
                "$group": {
                    "_id": "$payment_status",
                    "count": {"$sum": 1},
                    "total_cod": {"$sum": "$cod_amount"},
                    "total_shipping": {"$sum": "$shipping_cost"},
                    "total_net": {"$sum": "$net_to_merchant"}
                }
            }
        ]
        
        results = await db.orders.aggregate(pipeline).to_list(100)
        
        # Format response
        summary = {
            "unpaid": {"count": 0, "total_cod": 0, "total_shipping": 0, "total_net": 0},
            "collected_by_driver": {"count": 0, "total_cod": 0, "total_shipping": 0, "total_net": 0},
            "transferred_to_merchant": {"count": 0, "total_cod": 0, "total_shipping": 0, "total_net": 0},
            "returned": {"count": 0, "total_cod": 0, "total_shipping": 0, "total_net": 0}
        }
        
        for item in results:
            status = item["_id"]
            if status in summary:
                summary[status] = {
                    "count": item["count"],
                    "total_cod": round(item["total_cod"], 2),
                    "total_shipping": round(item["total_shipping"], 2),
                    "total_net": round(item["total_net"], 2)
                }
        
        # Calculate grand totals
        grand_total = {
            "total_orders": sum(s["count"] for s in summary.values()),
            "total_cod": sum(s["total_cod"] for s in summary.values()),
            "total_shipping": sum(s["total_shipping"] for s in summary.values()),
            "total_net": sum(s["total_net"] for s in summary.values())
        }
        
        return {
            "summary_by_status": summary,
            "grand_total": grand_total
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting financial summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reconciliation")
async def get_reconciliation_list(
    payment_status: str = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Get list of orders by payment status for reconciliation
    """
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Build query
        query = {}
        if payment_status:
            query["payment_status"] = payment_status
        
        # Get orders
        orders = await db.orders.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {
            "orders": orders,
            "count": len(orders),
            "filter": payment_status or "all"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reconciliation list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
