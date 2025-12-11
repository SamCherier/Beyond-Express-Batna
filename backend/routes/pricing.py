"""
Pricing Table Management Routes
Handles shipping cost calculation based on wilaya and delivery type
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from typing import List
import os
import logging

from models import PricingTable, PricingTableCreate, User, DeliveryType
from auth_utils import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

@router.get("/")
async def get_all_pricing():
    """
    Get all pricing entries (PUBLIC - needed for order creation)
    """
    try:
        pricing_list = await db.pricing_table.find({}, {"_id": 0}).to_list(1000)
        return {
            "pricing": pricing_list,
            "count": len(pricing_list)
        }
    except Exception as e:
        logger.error(f"Error getting pricing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calculate")
async def calculate_shipping_cost(
    wilaya: str,
    delivery_type: str = "home"
):
    """
    Calculate shipping cost for a given wilaya and delivery type
    Used during order creation to auto-fill shipping_cost
    """
    try:
        # Normalize delivery type
        delivery_type_enum = DeliveryType.HOME if delivery_type.lower() in ["home", "domicile"] else DeliveryType.DESK
        
        # Find pricing
        pricing = await db.pricing_table.find_one(
            {
                "wilaya": wilaya,
                "delivery_type": delivery_type_enum.value
            },
            {"_id": 0}
        )
        
        if not pricing:
            # Return default or raise error
            logger.warning(f"No pricing found for wilaya={wilaya}, delivery_type={delivery_type_enum.value}")
            return {
                "found": False,
                "wilaya": wilaya,
                "delivery_type": delivery_type_enum.value,
                "price": 0.0,
                "message": "No pricing configured for this wilaya/delivery type combination"
            }
        
        return {
            "found": True,
            "wilaya": pricing["wilaya"],
            "delivery_type": pricing["delivery_type"],
            "price": pricing["price"]
        }
    
    except Exception as e:
        logger.error(f"Error calculating shipping cost: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_or_update_pricing(
    pricing_data: PricingTableCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create or update pricing entry (Admin only)
    """
    try:
        # Only admins can manage pricing
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can manage pricing")
        
        # Check if entry exists
        existing = await db.pricing_table.find_one({
            "wilaya": pricing_data.wilaya,
            "delivery_type": pricing_data.delivery_type.value
        })
        
        if existing:
            # Update existing
            await db.pricing_table.update_one(
                {"id": existing["id"]},
                {"$set": {
                    "price": pricing_data.price,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            logger.info(f"✅ Pricing updated: {pricing_data.wilaya} - {pricing_data.delivery_type.value} = {pricing_data.price} DZD")
            return {
                "success": True,
                "action": "updated",
                "pricing": {
                    "wilaya": pricing_data.wilaya,
                    "delivery_type": pricing_data.delivery_type.value,
                    "price": pricing_data.price
                }
            }
        else:
            # Create new
            from uuid import uuid4
            new_pricing = {
                "id": str(uuid4()),
                "wilaya": pricing_data.wilaya,
                "delivery_type": pricing_data.delivery_type.value,
                "price": pricing_data.price,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            await db.pricing_table.insert_one(new_pricing)
            logger.info(f"✅ Pricing created: {pricing_data.wilaya} - {pricing_data.delivery_type.value} = {pricing_data.price} DZD")
            return {
                "success": True,
                "action": "created",
                "pricing": {
                    "id": new_pricing["id"],
                    "wilaya": pricing_data.wilaya,
                    "delivery_type": pricing_data.delivery_type.value,
                    "price": pricing_data.price
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/updating pricing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{pricing_id}")
async def delete_pricing(
    pricing_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a pricing entry (Admin only)
    """
    try:
        # Only admins can delete pricing
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can delete pricing")
        
        result = await db.pricing_table.delete_one({"id": pricing_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pricing entry not found")
        
        logger.info(f"✅ Pricing deleted: {pricing_id}")
        return {
            "success": True,
            "message": "Pricing entry deleted"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pricing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-create")
async def bulk_create_pricing(
    pricing_list: List[PricingTableCreate],
    current_user: User = Depends(get_current_user)
):
    """
    Bulk create pricing entries (Admin only)
    Useful for initial setup with all wilayas
    """
    try:
        # Only admins can bulk create
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can bulk create pricing")
        
        from uuid import uuid4
        now = datetime.now(timezone.utc)
        
        documents = []
        for pricing_data in pricing_list:
            # Check if exists
            existing = await db.pricing_table.find_one({
                "wilaya": pricing_data.wilaya,
                "delivery_type": pricing_data.delivery_type.value
            })
            
            if not existing:
                documents.append({
                    "id": str(uuid4()),
                    "wilaya": pricing_data.wilaya,
                    "delivery_type": pricing_data.delivery_type.value,
                    "price": pricing_data.price,
                    "created_at": now,
                    "updated_at": now
                })
        
        if documents:
            await db.pricing_table.insert_many(documents)
            logger.info(f"✅ Bulk pricing creation: {len(documents)} entries created")
        
        return {
            "success": True,
            "created_count": len(documents),
            "skipped_count": len(pricing_list) - len(documents),
            "message": f"{len(documents)} pricing entries created"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk create: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
