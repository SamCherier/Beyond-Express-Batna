"""
Carrier Integration Routes
Manage carrier API configurations and test connections
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from datetime import datetime, timezone
import os
import logging
from typing import List, Optional
import httpx
import time
import uuid

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

# Auth dependency - direct auth extraction (same as returns.py)
async def _auth_carrier(request):
    from auth_utils import verify_token
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session_doc = await db.sessions.find_one({"session_token": token}, {"_id": 0})
    if session_doc:
        from datetime import datetime, timezone
        if datetime.fromisoformat(session_doc['expires_at']) > datetime.now(timezone.utc):
            user_doc = await db.users.find_one({"id": session_doc['user_id']}, {"_id": 0})
            if user_doc:
                return User(**user_doc)
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_doc = await db.users.find_one({"id": payload.get("sub")}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user_doc)

def get_current_user():
    """Legacy wrapper - used by Depends() in route definitions"""
    from server import get_current_user as _gcu
    return _gcu

# ===== TEST CONNECTION ENDPOINT =====

class TestConnectionRequest(BaseModel):
    base_url: str
    auth_header_name: str
    auth_header_value: str
    test_endpoint: Optional[str] = "/"

@router.post("/test-connection")
async def test_carrier_connection(request: TestConnectionRequest):
    """
    Test connection to a carrier API
    Returns detailed error information for debugging
    """
    try:
        # Build full URL
        url = f"{request.base_url.rstrip('/')}/{request.test_endpoint.lstrip('/')}"
        
        # Build headers
        headers = {
            request.auth_header_name: request.auth_header_value
        }
        
        start_time = time.time()
        
        # Make test request
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, headers=headers)
                response_time = round((time.time() - start_time) * 1000)  # ms
                
                # Success cases (200-299)
                if 200 <= response.status_code < 300:
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "message": "✅ Connexion réussie !",
                        "response_time_ms": response_time,
                        "details": f"API accessible. Temps de réponse : {response_time}ms"
                    }
                
                # Authentication errors
                elif response.status_code in [401, 403]:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "message": "❌ Clé invalide ou accès refusé",
                        "response_time_ms": response_time,
                        "details": f"Code {response.status_code}: Vérifiez votre clé API et vos permissions. Réponse: {response.text[:200]}"
                    }
                
                # Not found
                elif response.status_code == 404:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "message": "⚠️ URL incorrecte",
                        "response_time_ms": response_time,
                        "details": f"L'endpoint '{url}' n'existe pas. Vérifiez l'URL de base."
                    }
                
                # Other errors
                else:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "message": f"⚠️ Erreur API ({response.status_code})",
                        "response_time_ms": response_time,
                        "details": f"Réponse: {response.text[:200]}"
                    }
                    
            except httpx.ConnectError as e:
                return {
                    "success": False,
                    "status_code": 0,
                    "message": "⚠️ Erreur de connexion",
                    "details": f"Impossible de se connecter à '{request.base_url}'. Vérifiez l'URL et votre connexion internet. Erreur: {str(e)}"
                }
            
            except httpx.TimeoutException:
                return {
                    "success": False,
                    "status_code": 0,
                    "message": "⚠️ Timeout",
                    "details": f"L'API ne répond pas (timeout après 10s). Vérifiez que l'URL est correcte."
                }
            
            except Exception as e:
                return {
                    "success": False,
                    "status_code": 0,
                    "message": "⚠️ Erreur réseau",
                    "details": f"Erreur lors de la connexion: {str(e)}"
                }
    
    except Exception as e:
        logger.error(f"Test connection error: {e}")
        return {
            "success": False,
            "status_code": 0,
            "message": "❌ Erreur système",
            "details": f"Erreur interne: {str(e)}"
        }

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
async def get_available_carriers(request: Request):
    """
    Get list of available carriers with configuration status
    SECURED - Requires authentication
    """
    user = await _auth_carrier(request)
    try:
        # For public view, return carriers without user-specific config
        # If you want user-specific config, add authentication back
        
        # List of all available carriers
        carriers = [
            {
                "carrier_type": "yalidine",
                "name": "Yalidine",
                "logo_url": "/carriers/yalidine.png",
                "description": "Service de livraison rapide à domicile",
                "is_configured": False,
                "is_active": False,
                "required_fields": ["api_key", "center_id"]
            },
            {
                "carrier_type": "dhd",
                "name": "DHD Express",  
                "logo_url": "/carriers/dhd.png",
                "description": "Domicile & Home Delivery",
                "is_configured": False,
                "is_active": False,
                "required_fields": ["api_key", "user_id"]
            },
            {
                "carrier_type": "zr_express",
                "name": "ZR Express",
                "logo_url": "/carriers/zr_express.png",
                "description": "Express delivery service",
                "is_configured": False,
                "is_active": False,
                "required_fields": ["api_key", "center_id"]
            },
            {
                "carrier_type": "maystro",
                "name": "Maystro",
                "logo_url": "/carriers/maystro.png",
                "description": "Service de livraison professionnel",
                "is_configured": False,
                "is_active": False,
                "required_fields": ["api_key"]
            },
            {
                "carrier_type": "guepex",
                "name": "Guepex",
                "logo_url": "/carriers/guepex.png",
                "description": "Livraison nationale",
                "is_configured": False,
                "is_active": False,
                "required_fields": ["api_key", "api_secret"]
            },
            {
                "carrier_type": "nord_ouest",
                "name": "Nord et Ouest",
                "logo_url": "/carriers/nord_ouest.png",
                "description": "Livraison régionale",
                "is_configured": False,
                "is_active": False,
                "required_fields": ["api_key"]
            },
            {
                "carrier_type": "pajo",
                "name": "Pajo",
                "logo_url": "/carriers/pajo.png",
                "description": "Service de livraison moderne",
                "is_configured": False,
                "is_active": False,
                "required_fields": ["api_key", "api_token"]
            },
        ]
        
        return carriers
    
    except Exception as e:
        logger.error(f"Error getting carriers: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get carriers")

@router.get("/{carrier_type}")
async def get_carrier_config(
    carrier_type: str,
    current_user: User = Depends(get_current_user)
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

@router.post("")
async def create_carrier_config(
    config_data: CarrierConfigCreate,
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
):
    """
    Test connection to a carrier API using our carrier services
    """
    try:
        carrier_type = test_request.carrier_type.value
        credentials = test_request.credentials
        test_mode = test_request.test_mode
        
        start_time = time.time()
        
        # Use our carrier implementation for proper testing
        if carrier_type == "yalidine":
            from services.carriers.yalidine import YalidineCarrier
            
            creds = {
                "api_key": credentials.api_key or "",
                "api_token": credentials.api_token or credentials.center_id or "",
                "center_id": credentials.center_id or ""
            }
            
            carrier = YalidineCarrier(creds, test_mode)
            is_valid = await carrier.validate_credentials()
            
            response_time = (time.time() - start_time) * 1000
            
            if is_valid:
                # Update config with test success
                await db.carrier_configs.update_one(
                    {"user_id": current_user.id, "carrier_type": carrier_type},
                    {
                        "$set": {
                            "last_test_status": "success",
                            "last_test_at": datetime.now(timezone.utc).isoformat(),
                            "last_test_message": "Connexion réussie",
                            "is_active": True  # Auto-activate on successful test
                        }
                    },
                    upsert=False
                )
                
                return TestConnectionResponse(
                    success=True,
                    status=CarrierStatus.ACTIVE,
                    message="✅ Connexion Yalidine réussie! API opérationnelle.",
                    response_time_ms=response_time
                )
            else:
                return TestConnectionResponse(
                    success=False,
                    status=CarrierStatus.ERROR,
                    message="❌ Échec d'authentification Yalidine. Vérifiez vos identifiants API.",
                    response_time_ms=response_time
                )
        
        # Fallback for other carriers - use generic HTTP test
        endpoints = CARRIER_TEST_ENDPOINTS.get(test_request.carrier_type)
        if not endpoints:
            return TestConnectionResponse(
                success=False,
                status=CarrierStatus.ERROR,
                message=f"Transporteur {carrier_type} non encore supporté pour les tests API"
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
        logger.error(f"Error testing carrier: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to test connection")


# ============================================
# GENERIC API BUILDER (ADMIN ONLY)
# ============================================

class GenericCarrierCreate(BaseModel):
    name: str
    base_url: str
    auth_type: str = "bearer"  # bearer, api_key, basic, custom_header
    auth_header_name: str = "Authorization"
    auth_header_template: str = "Bearer {KEY}"
    api_key: str = ""
    secret_key: str = ""
    logo_color: str = "#1E3A8A"
    create_shipment_endpoint: str = "/shipments"
    track_shipment_endpoint: str = "/tracking/{tracking_id}"
    tracking_id_field: str = "tracking_id"
    status_field: str = "status"


@router.get("/generic")
async def get_generic_carriers(
    current_user: User = Depends(get_current_user)
):
    """
    Get all generic/custom carrier configurations
    ADMIN ONLY
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only feature")
    
    try:
        generic_configs = await db.generic_carriers.find(
            {"user_id": current_user.id},
            {"_id": 0}
        ).to_list(100)
        
        return {
            "success": True,
            "carriers": generic_configs
        }
    except Exception as e:
        logger.error(f"Error fetching generic carriers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generic")
async def create_generic_carrier(
    config: GenericCarrierCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new generic/custom carrier configuration
    ADMIN ONLY - Allows adding any carrier without coding
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only feature")
    
    try:
        import uuid
        
        # Generate safe ID from name
        carrier_id = config.name.lower().replace(" ", "_").replace("-", "_")
        carrier_id = "".join(c for c in carrier_id if c.isalnum() or c == "_")
        
        # Check if already exists
        existing = await db.generic_carriers.find_one({
            "user_id": current_user.id,
            "carrier_id": carrier_id
        })
        
        if existing:
            raise HTTPException(status_code=400, detail=f"Carrier '{config.name}' already exists")
        
        now = datetime.now(timezone.utc).isoformat()
        
        carrier_doc = {
            "id": str(uuid.uuid4()),
            "carrier_id": carrier_id,
            "user_id": current_user.id,
            "name": config.name,
            "base_url": config.base_url,
            "auth_type": config.auth_type,
            "auth_header_name": config.auth_header_name,
            "auth_header_template": config.auth_header_template,
            "api_key": config.api_key,
            "secret_key": config.secret_key,
            "logo_color": config.logo_color,
            "create_shipment_endpoint": config.create_shipment_endpoint,
            "track_shipment_endpoint": config.track_shipment_endpoint,
            "tracking_id_field": config.tracking_id_field,
            "status_field": config.status_field,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        
        await db.generic_carriers.insert_one(carrier_doc)
        
        logger.info(f"✅ Generic carrier '{config.name}' created by {current_user.email}")
        
        return {
            "success": True,
            "message": f"Carrier '{config.name}' added successfully",
            "carrier_id": carrier_id,
            "id": carrier_doc["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating generic carrier: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/generic/{carrier_id}")
async def delete_generic_carrier(
    carrier_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a generic carrier configuration - ADMIN ONLY"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only feature")
    
    try:
        result = await db.generic_carriers.delete_one({
            "user_id": current_user.id,
            "carrier_id": carrier_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Carrier not found")
        
        return {"success": True, "message": "Carrier deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Pre-configured carriers available for quick setup
@router.get("/preconfigured")
async def get_preconfigured_carriers():
    """
    Get list of pre-configured carriers that can be quickly added
    """
    return {
        "carriers": [
            {
                "id": "anderson",
                "name": "Anderson Logistics",
                "description": "Service logistique algérien premium",
                "logo_color": "#1E3A8A",
                "requires": ["api_key", "secret_key"]
            },
            {
                "id": "speedz",
                "name": "SpeedZ Express",
                "description": "Livraison express Algérie",
                "logo_color": "#10B981",
                "requires": ["api_key"]
            },
            {
                "id": "ecotrack",
                "name": "EcoTrack",
                "description": "Livraison écologique",
                "logo_color": "#059669",
                "requires": ["api_key", "api_token"]
            }
        ]
    }
