"""
Subscription and Plans API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import os
import logging
from typing import List, Optional
import uuid

from models import Plan, Subscription, PlanType, BillingPeriod, SubscriptionStatus, User

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Import auth dependency (will be injected at runtime from server.py)
# This is a placeholder - the actual dependency will come from server.py
get_current_user_dependency = None

def set_auth_dependency(dependency):
    """Set the auth dependency from server.py"""
    global get_current_user_dependency
    get_current_user_dependency = dependency

@router.get("/plans")
async def get_all_plans():
    """
    Get all available subscription plans
    Public endpoint - no authentication required
    """
    try:
        plans_collection = db["plans"]
        cursor = plans_collection.find(
            {"is_active": True},
            {"_id": 0}
        ).sort("display_order", 1)
        
        plans = []
        async for plan in cursor:
            # Convert datetime to ISO string
            if "created_at" in plan:
                plan["created_at"] = plan["created_at"].isoformat()
            if "updated_at" in plan:
                plan["updated_at"] = plan["updated_at"].isoformat()
            plans.append(plan)
        
        return {"plans": plans, "total": len(plans)}
    except Exception as e:
        logger.error(f"Error fetching plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch plans")

@router.get("/plans/{plan_type}")
async def get_plan_by_type(plan_type: str):
    """
    Get specific plan details by type
    """
    try:
        plans_collection = db["plans"]
        plan = await plans_collection.find_one(
            {"plan_type": plan_type, "is_active": True},
            {"_id": 0}
        )
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Convert datetime to ISO string
        if "created_at" in plan:
            plan["created_at"] = plan["created_at"].isoformat()
        if "updated_at" in plan:
            plan["updated_at"] = plan["updated_at"].isoformat()
        
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch plan")

@router.post("/subscribe")
async def subscribe_to_plan(
    plan_type: str,
    billing_period: str = "monthly",
    current_user: User = Depends(lambda: get_current_user_dependency)
):
    """
    Subscribe to a plan (SIMULATION - no real payment)
    
    Simulates the subscription process without actual payment integration.
    In production, integrate with payment provider (Stripe, CCP, etc.)
    """
    try:
        user_id = current_user.id
        
        # Fetch the plan
        plans_collection = db["plans"]
        plan = await plans_collection.find_one(
            {"plan_type": plan_type, "is_active": True},
            {"_id": 0}
        )
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Calculate dates
        now = datetime.now(timezone.utc)
        
        if billing_period == "monthly":
            end_date = now + timedelta(days=30)
            amount = plan["pricing"]["monthly_price"]
        elif billing_period == "quarterly":
            end_date = now + timedelta(days=90)
            amount = plan["pricing"].get("quarterly_price", plan["pricing"]["monthly_price"] * 3)
        elif billing_period == "biannual":
            end_date = now + timedelta(days=180)
            amount = plan["pricing"].get("biannual_price", plan["pricing"]["monthly_price"] * 6)
        elif billing_period == "annual":
            end_date = now + timedelta(days=365)
            amount = plan["pricing"].get("annual_price", plan["pricing"]["monthly_price"] * 12)
        else:
            raise HTTPException(status_code=400, detail="Invalid billing period")
        
        # Create subscription
        subscription = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "plan_id": plan.get("id", plan_type),
            "plan_type": plan_type,
            "billing_period": billing_period,
            "status": "active",  # Auto-active in simulation
            "start_date": now,
            "end_date": end_date,
            "amount_paid": amount,
            "payment_method": "simulation",
            "auto_renew": False,
            "created_at": now,
            "updated_at": now
        }
        
        subscriptions_collection = db["subscriptions"]
        await subscriptions_collection.insert_one(subscription.copy())
        
        # Update user's current plan
        users_collection = db["users"]
        await users_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "current_plan": plan_type,
                    "plan_expires_at": end_date,
                    "subscription_id": subscription["id"]
                }
            }
        )
        
        logger.info(f"✅ User {user_id} subscribed to {plan_type}")
        
        return {
            "success": True,
            "message": f"Successfully subscribed to {plan['name_fr']}",
            "subscription": subscription,
            "expires_at": end_date.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")

@router.get("/my-subscription")
async def get_my_subscription(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Get current user's active subscription
    """
    try:
        user_id = current_user.id
        
        subscriptions_collection = db["subscriptions"]
        subscription = await subscriptions_collection.find_one(
            {"user_id": user_id, "status": "active"},
            {"_id": 0}
        )
        
        if not subscription:
            return {
                "has_subscription": False,
                "current_plan": "free",
                "message": "No active subscription"
            }
        
        # Convert datetime to ISO
        if "start_date" in subscription:
            subscription["start_date"] = subscription["start_date"].isoformat()
        if "end_date" in subscription:
            subscription["end_date"] = subscription["end_date"].isoformat()
        if "created_at" in subscription:
            subscription["created_at"] = subscription["created_at"].isoformat()
        if "updated_at" in subscription:
            subscription["updated_at"] = subscription["updated_at"].isoformat()
        
        return {
            "has_subscription": True,
            "subscription": subscription
        }
    
    except Exception as e:
        logger.error(f"Error fetching subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscription")

@router.get("/check-limit/{feature}")
async def check_feature_limit(
    feature: str,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Check if current user has reached limit for a feature
    
    Features: orders, delivery_companies, stock_items, whatsapp, ai_generator
    """
    try:
        user_id = current_user.id
        current_plan_type = current_user.current_plan  # Get from user object
        
        # Get plan details
        plans_collection = db["plans"]
        plan = await plans_collection.find_one(
            {"plan_type": current_plan_type},
            {"_id": 0}
        )
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        features = plan.get("features", {})
        
        # Return feature-specific limits
        result = {
            "plan_type": current_plan_type,
            "feature": feature,
            "has_access": True,
            "limit": None,
            "current_usage": 0
        }
        
        if feature == "orders":
            result["limit"] = features.get("max_orders_per_month", 0)
        elif feature == "delivery_companies":
            result["limit"] = features.get("max_delivery_companies", 1)
        elif feature == "whatsapp":
            result["has_access"] = features.get("whatsapp_auto_confirmation", False)
        elif feature == "ai_generator":
            result["has_access"] = features.get("ai_content_generator", False)
            result["limit"] = features.get("ai_generator_uses", 0)
        elif feature == "pro_dashboard":
            result["has_access"] = features.get("pro_dashboard", False)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking feature limit: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check limit")

@router.post("/cancel")
async def cancel_subscription(
    cancellation_reason: Optional[str] = None,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Cancel current user's active subscription
    """
    try:
        user_id = current_user.id
        
        # Find active subscription
        subscriptions_collection = db["subscriptions"]
        subscription = await subscriptions_collection.find_one(
            {"user_id": user_id, "status": "active"},
            {"_id": 0}
        )
        
        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        # Update subscription to cancelled
        now = datetime.now(timezone.utc)
        await subscriptions_collection.update_one(
            {"id": subscription["id"]},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": now,
                    "cancellation_reason": cancellation_reason or "User requested",
                    "updated_at": now
                }
            }
        )
        
        # Revert user to FREE plan
        users_collection = db["users"]
        await users_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "current_plan": "free",
                    "plan_expires_at": None,
                    "subscription_id": None
                }
            }
        )
        
        logger.info(f"✅ User {user_id} cancelled subscription {subscription['id']}")
        
        return {
            "success": True,
            "message": "Subscription cancelled successfully. Reverted to FREE plan.",
            "previous_plan": subscription["plan_type"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

@router.post("/upgrade")
async def upgrade_subscription(
    new_plan_type: str,
    new_billing_period: str = "monthly",
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Upgrade or downgrade to a different plan
    
    This will:
    1. Cancel the current subscription
    2. Create a new subscription with the new plan
    """
    try:
        user_id = current_user.id
        
        # Validate new plan exists
        plans_collection = db["plans"]
        new_plan = await plans_collection.find_one(
            {"plan_type": new_plan_type, "is_active": True},
            {"_id": 0}
        )
        
        if not new_plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Find current active subscription
        subscriptions_collection = db["subscriptions"]
        current_subscription = await subscriptions_collection.find_one(
            {"user_id": user_id, "status": "active"},
            {"_id": 0}
        )
        
        old_plan_type = current_subscription["plan_type"] if current_subscription else "free"
        
        # Cancel old subscription if exists
        if current_subscription:
            now = datetime.now(timezone.utc)
            await subscriptions_collection.update_one(
                {"id": current_subscription["id"]},
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelled_at": now,
                        "cancellation_reason": f"Upgraded to {new_plan_type}",
                        "updated_at": now
                    }
                }
            )
        
        # Create new subscription
        now = datetime.now(timezone.utc)
        
        if new_billing_period == "monthly":
            end_date = now + timedelta(days=30)
            amount = new_plan["pricing"]["monthly_price"]
        elif new_billing_period == "quarterly":
            end_date = now + timedelta(days=90)
            amount = new_plan["pricing"].get("quarterly_price", new_plan["pricing"]["monthly_price"] * 3)
        elif new_billing_period == "biannual":
            end_date = now + timedelta(days=180)
            amount = new_plan["pricing"].get("biannual_price", new_plan["pricing"]["monthly_price"] * 6)
        elif new_billing_period == "annual":
            end_date = now + timedelta(days=365)
            amount = new_plan["pricing"].get("annual_price", new_plan["pricing"]["monthly_price"] * 12)
        else:
            raise HTTPException(status_code=400, detail="Invalid billing period")
        
        new_subscription = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "plan_id": new_plan.get("id", new_plan_type),
            "plan_type": new_plan_type,
            "billing_period": new_billing_period,
            "status": "active",
            "start_date": now,
            "end_date": end_date,
            "amount_paid": amount,
            "payment_method": "simulation",
            "auto_renew": False,
            "created_at": now,
            "updated_at": now
        }
        
        await subscriptions_collection.insert_one(new_subscription.copy())
        
        # Update user's plan
        users_collection = db["users"]
        await users_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "current_plan": new_plan_type,
                    "plan_expires_at": end_date,
                    "subscription_id": new_subscription["id"]
                }
            }
        )
        
        logger.info(f"✅ User {user_id} upgraded from {old_plan_type} to {new_plan_type}")
        
        return {
            "success": True,
            "message": f"Successfully {'upgraded' if old_plan_type == 'free' else 'changed'} to {new_plan['name_fr']}",
            "old_plan": old_plan_type,
            "new_plan": new_plan_type,
            "subscription": new_subscription,
            "expires_at": end_date.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upgrading subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upgrade subscription")
