"""
Carrier Integration Routes
Manage carrier API configurations and test connections
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import logging
from typing import List
import httpx
import time

from models import (
    CarrierConfig, CarrierConfigCreate, CarrierConfigUpdate,
    TestConnectionRequest, TestConnectionResponse,
    CarrierType, CarrierStatus, User
)

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Auth dependency placeholder
async def get_current_user_dependency():
    """Placeholder - will be replaced by actual dependency from server.py"""
    raise HTTPException(status_code=500, detail="Auth dependency not configured")

# Carrier API endpoints (test endpoints)
CARRIER_TEST_ENDPOINTS = {
    CarrierType.YALIDINE: {
        "production": "https://api.yalidine.app/v1/parcels",
        "sandbox": "https://sandbox.yalidine.app/v1/parcels"
    },
    CarrierType.DHD: {
        "production": "https://api.dhd-dz.com/v1/shipments",
        "sandbox": "https://sandbox.dhd-dz.com/v1/shipments"
    },
    CarrierType.ZR_EXPRESS: {
        "production": "https://api.zrexpress.dz/v1/orders",
        "sandbox": "https://sandbox.zrexpress.dz/v1/orders"
    },
    # Add more carriers as needed
}

@router.get("", response_model=List[dict])
async def get_available_carriers(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Get list of available carriers with configuration status
    """
    try:
        user_id = current_user.id
        
        # Get user's configured carriers
        configs_collection = db["carrier_configs"]
        user_configs = await configs_collection.find({"user_id": user_id}).to_list(length=None)
        
        # Map of carrier_type to config
        config_map = {config["carrier_type"]: config for config in user_configs}
        
        # List of all available carriers
        carriers = [
            {
                "carrier_type": "yalidine",
                "name": "Yalidine",
                "logo": "/carriers/yalidine.png",
                "description": "Service de livraison rapide à domicile",
                "is_configured": "yalidine" in config_map,
                "is_active": config_map.get("yalidine", {}).get("is_active", False),
                "required_fields": ["api_key", "api_token"]
            },
            {
                "carrier_type": "dhd",
                "name": "DHD",
                "logo": "/carriers/dhd.png",
                "description": "Domicile & Home Delivery",
                "is_configured": "dhd" in config_map,
                "is_active": config_map.get("dhd", {}).get("is_active", False),
                "required_fields": ["api_key", "user_id"]
            },
            {
                "carrier_type": "zr_express",
                "name": "ZR Express",
                "logo": "/carriers/zr_express.png",
                "description": "Express delivery service",
                "is_configured": "zr_express" in config_map,
                "is_active": config_map.get("zr_express", {}).get("is_active", False),
                "required_fields": ["api_key", "center_id"]
            },
            {
                "carrier_type": "maystro",
                "name": "Maystro Delivery",
                "logo": "/carriers/maystro.png",
                "description": "Service de livraison professionnel",
                "is_configured": "maystro" in config_map,
                "is_active": config_map.get("maystro", {}).get("is_active", False),
                "required_fields": ["api_key"]
            },
            {
                "carrier_type": "guepex",
                "name": "Guepex",
                "logo": "/carriers/guepex.png",
                "description": "Livraison nationale",
                "is_configured": "guepex" in config_map,
                "is_active": config_map.get("guepex", {}).get("is_active", False),
                "required_fields": ["api_key", "api_secret"]
            },
        ]
        
        return carriers
    
    except Exception as e:
        logger.error(f"Error getting carriers: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get carriers")

@router.get("/{carrier_type}")
async def get_carrier_config(
    carrier_type: str,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Get configuration for a specific carrier
    """
    try:
        user_id = current_user.id
        
        configs_collection = db["carrier_configs"]
        config = await configs_collection.find_one(
            {"user_id": user_id, "carrier_type": carrier_type},
            {"_id": 0}
        )
        
        if not config:
            raise HTTPException(status_code=404, detail="Carrier not configured")
        
        # Don't send sensitive data
        if "credentials" in config:
            # Mask credentials
            if config["credentials"].get("api_key"):
                config["credentials"]["api_key"] = "****" + config["credentials"]["api_key"][-4:]
            if config["credentials"].get("api_token"):
                config["credentials"]["api_token"] = "****"
            if config["credentials"].get("api_secret"):
                config["credentials"]["api_secret"] = "****"
        
        return config
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting carrier config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get carrier config")

@router.post("/carriers")
async def create_carrier_config(
    config_data: CarrierConfigCreate,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Create or update carrier configuration
    """
    try:
        user_id = current_user.id
        carrier_type = config_data.carrier_type.value
        
        # Get carrier name
        carrier_names = {
            "yalidine": "Yalidine",
            "dhd": "DHD",
            "zr_express": "ZR Express",
            "maystro": "Maystro Delivery",
            "guepex": "Guepex"
        }
        
        configs_collection = db["carrier_configs"]
        
        # Check if config already exists
        existing = await configs_collection.find_one({
            "user_id": user_id,
            "carrier_type": carrier_type
        })
        
        now = datetime.now(timezone.utc)
        
        config = {
            "user_id": user_id,
            "carrier_type": carrier_type,
            "carrier_name": carrier_names.get(carrier_type, carrier_type.title()),
            "is_active": False,  # Inactive by default until tested
            "credentials": config_data.credentials.dict(),
            "test_mode": config_data.test_mode,
            "last_test_status": None,
            "last_test_at": None,
            "last_test_message": None,
            "updated_at": now
        }
        
        if existing:
            # Update existing
            config["id"] = existing["id"]
            config["created_at"] = existing["created_at"]
            await configs_collection.update_one(
                {"id": existing["id"]},
                {"$set": config}
            )
            message = "Configuration updated"
        else:
            # Create new
            import uuid
            config["id"] = str(uuid.uuid4())
            config["created_at"] = now
            await configs_collection.insert_one(config.copy())
            message = "Configuration created"
        
        logger.info(f"✅ Carrier config {message} for user {user_id}, carrier {carrier_type}")
        
        return {
            "success": True,
            "message": message,
            "config_id": config["id"]
        }
    
    except Exception as e:
        logger.error(f"Error creating carrier config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create carrier config")

@router.post("/test-connection")
async def test_carrier_connection(
    test_request: TestConnectionRequest,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Test connection to a carrier API
    """
    try:
        carrier_type = test_request.carrier_type.value
        credentials = test_request.credentials
        test_mode = test_request.test_mode
        
        # Get API endpoint
        endpoints = CARRIER_TEST_ENDPOINTS.get(test_request.carrier_type)
        if not endpoints:
            return TestConnectionResponse(
                success=False,
                status=CarrierStatus.ERROR,
                message=f"Carrier {carrier_type} not yet supported for API testing"
            )
        
        endpoint = endpoints.get("sandbox" if test_mode else "production")
        
        # Perform test request
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Build headers based on carrier
                headers = {
                    "Content-Type": "application/json"
                }
                
                if carrier_type == "yalidine":
                    headers["X-API-Key"] = credentials.api_key or ""
                    headers["X-API-Token"] = credentials.api_token or ""
                elif carrier_type == "dhd":
                    headers["Authorization"] = f"Bearer {credentials.api_key}"
                    headers["X-User-ID"] = credentials.user_id or ""
                elif carrier_type == "zr_express":
                    headers["X-API-Key"] = credentials.api_key or ""
                    headers["X-Center-ID"] = credentials.center_id or ""
                
                # Make test GET request
                response = await client.get(endpoint, headers=headers)
                
                response_time = (time.time() - start_time) * 1000  # ms
                
                if response.status_code in [200, 201]:
                    return TestConnectionResponse(
                        success=True,
                        status=CarrierStatus.ACTIVE,
                        message="✅ Connection successful! API is reachable.",
                        response_time_ms=response_time
                    )
                elif response.status_code == 401:
                    return TestConnectionResponse(
                        success=False,
                        status=CarrierStatus.ERROR,
                        message="❌ Authentication failed. Please check your API credentials.",
                        response_time_ms=response_time
                    )
                else:
                    return TestConnectionResponse(
                        success=False,
                        status=CarrierStatus.ERROR,
                        message=f"❌ API returned status {response.status_code}",
                        response_time_ms=response_time
                    )
        
        except httpx.TimeoutException:
            return TestConnectionResponse(
                success=False,
                status=CarrierStatus.ERROR,
                message="⏱️ Connection timeout. API did not respond in time."
            )
        except Exception as e:
            return TestConnectionResponse(
                success=False,
                status=CarrierStatus.ERROR,
                message=f"❌ Connection error: {str(e)}"
            )
    
    except Exception as e:
        logger.error(f"Error testing carrier connection: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to test connection")

@router.put("/carriers/{carrier_type}/toggle")
async def toggle_carrier_status(
    carrier_type: str,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Toggle carrier active status
    """
    try:
        user_id = current_user.id
        
        configs_collection = db["carrier_configs"]
        config = await configs_collection.find_one({
            "user_id": user_id,
            "carrier_type": carrier_type
        })
        
        if not config:
            raise HTTPException(status_code=404, detail="Carrier not configured")
        
        new_status = not config.get("is_active", False)
        
        await configs_collection.update_one(
            {"id": config["id"]},
            {"$set": {"is_active": new_status, "updated_at": datetime.now(timezone.utc)}}
        )
        
        logger.info(f"✅ Carrier {carrier_type} {'activated' if new_status else 'deactivated'} for user {user_id}")
        
        return {
            "success": True,
            "is_active": new_status,
            "message": f"Carrier {'activated' if new_status else 'deactivated'}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling carrier status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to toggle carrier status")

@router.delete("/carriers/{carrier_type}")
async def delete_carrier_config(
    carrier_type: str,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Delete carrier configuration
    """
    try:
        user_id = current_user.id
        
        configs_collection = db["carrier_configs"]
        result = await configs_collection.delete_one({
            "user_id": user_id,
            "carrier_type": carrier_type
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Carrier configuration not found")
        
        logger.info(f"✅ Carrier config deleted for user {user_id}, carrier {carrier_type}")
        
        return {
            "success": True,
            "message": "Carrier configuration deleted"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting carrier config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete carrier config")
