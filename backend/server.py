from fastapi import FastAPI, APIRouter, HTTPException, Depends, Response, Request, Cookie, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import requests
import secrets

from models import *
from auth_utils import hash_password, verify_password, create_access_token, verify_token, generate_session_token
from pdf_generator_yalidine import generate_bordereau_pdf_yalidine_format as generate_bordereau_pdf
from emergentintegrations.llm.chat import LlmChat, UserMessage
from audit_logger import AuditLogger, AuditAction
from routes import whatsapp as whatsapp_router
from routes import subscriptions as subscriptions_router
from routes import ai_assistant as ai_assistant_router
from routes import carriers as carriers_router
from routes import shipping as shipping_router
from routes import webhooks as webhooks_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')


# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize Audit Logger
audit_logger = AuditLogger(db)

# Create the main app without a prefix
app = FastAPI()

# Mount uploads directory for serving images
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
(UPLOAD_DIR / "profile_pictures").mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Auth dependency
async def get_current_user(request: Request, session_token: Optional[str] = Cookie(None)) -> User:
    token = session_token
    
    # Fallback to Authorization header if cookie not present
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Try session token first
    session_doc = await db.sessions.find_one({"session_token": token}, {"_id": 0})
    if session_doc:
        if datetime.fromisoformat(session_doc['expires_at']) > datetime.now(timezone.utc):
            user_doc = await db.users.find_one({"id": session_doc['user_id']}, {"_id": 0})
            if user_doc:
                return User(**user_doc)
    
    # Try JWT token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)

# Admin dependency
async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ===== AUTH ROUTES =====
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate, request: Request):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_pw = hash_password(user_data.password)
    
    # Create user
    user_obj = User(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role
    )
    user_dict = user_obj.model_dump()
    user_dict['password'] = hashed_pw
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Log user creation
    await audit_logger.log_action(
        action=AuditAction.CREATE_USER,
        user_id=user_obj.id,
        user_email=user_data.email,
        details={"role": user_data.role},
        ip_address=request.client.host if request.client else None,
        status="success"
    )
    
    return user_obj

@api_router.post("/auth/login")
async def login(credentials: UserLogin, response: Response, request: Request):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc:
        # Log failed login attempt
        await audit_logger.log_action(
            action=AuditAction.FAILED_LOGIN,
            user_id="unknown",
            user_email=credentials.email,
            details={"reason": "User not found"},
            ip_address=request.client.host if request.client else None,
            status="failed"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user_doc['password']):
        # Log failed login attempt
        await audit_logger.log_action(
            action=AuditAction.FAILED_LOGIN,
            user_id=user_doc['id'],
            user_email=credentials.email,
            details={"reason": "Invalid password"},
            ip_address=request.client.host if request.client else None,
            status="failed"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user_doc['id']})
    
    # Create session - Extended to 30 days for stable demo
    session_token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    
    session_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_doc['id'],
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sessions.insert_one(session_doc)
    
    # Set cookie - 30 days, cross-origin compatible
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=30 * 24 * 60 * 60,  # 30 days
        path="/",
        httponly=True,
        samesite="none",  # Required for cross-origin
        secure=True  # Required for SameSite=None
    )
    
    user_obj = User(**{k: v for k, v in user_doc.items() if k != 'password'})
    
    # Log successful login
    await audit_logger.log_action(
        action=AuditAction.LOGIN,
        user_id=user_doc['id'],
        user_email=credentials.email,
        details={"method": "password"},
        ip_address=request.client.host if request.client else None,
        status="success"
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_obj
    }

@api_router.post("/auth/google-session")
async def process_google_session(request: Request, response: Response):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Call Emergent auth service
    auth_response = requests.get(
        "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
        headers={"X-Session-ID": session_id}
    )
    
    if auth_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    session_data = auth_response.json()
    
    # Check if user exists
    user_doc = await db.users.find_one({"email": session_data['email']}, {"_id": 0})
    
    if not user_doc:
        # Create new user (default ecommerce role)
        user_obj = User(
            email=session_data['email'],
            name=session_data['name'],
            role=UserRole.ECOMMERCE,
            picture=session_data.get('picture')
        )
        user_dict = user_obj.model_dump()
        user_dict['password'] = hash_password(secrets.token_urlsafe(32))
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        await db.users.insert_one(user_dict)
        user_doc = user_dict
    
    # Create session - Extended to 30 days for stable demo
    session_token = session_data['session_token']
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    
    session_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_doc['id'],
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sessions.insert_one(session_doc)
    
    # Set cookie - 30 days, cross-origin compatible
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=30 * 24 * 60 * 60,  # 30 days
        path="/",
        httponly=True,
        samesite="none",  # Required for cross-origin
        secure=True  # Required for SameSite=None
    )
    
    user_obj = User(**{k: v for k, v in user_doc.items() if k != 'password'})
    
    return {
        "user": user_obj,
        "session_token": session_token
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response, session_token: Optional[str] = Cookie(None)):
    """Logout current session - works even without valid auth"""
    token = session_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    user_id = None
    user_email = None

    if token:
        # Find session to get user info for audit
        sess = await db.sessions.find_one({"session_token": token}, {"_id": 0})
        if sess:
            user_id = sess.get("user_id")
            u = await db.users.find_one({"id": user_id}, {"_id": 0})
            if u:
                user_email = u.get("email")
        # Delete this session
        await db.sessions.delete_one({"session_token": token})

    response.delete_cookie(key="session_token", path="/")
    response.delete_cookie(key="session_token", path="/", domain=None)

    if user_id:
        await audit_logger.log_action(
            action=AuditAction.LOGOUT,
            user_id=user_id,
            user_email=user_email or "unknown",
            status="success"
        )

    return {"message": "Logged out successfully"}


@api_router.post("/auth/logout-all")
async def logout_all_devices(request: Request, response: Response):
    """Logout from ALL devices - invalidate every session for this user"""
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    cookie_token = request.cookies.get("session_token")
    if cookie_token:
        token = cookie_token

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Find user from session or JWT
    user_id = None
    sess = await db.sessions.find_one({"session_token": token}, {"_id": 0})
    if sess:
        user_id = sess.get("user_id")
    else:
        payload = verify_token(token)
        if payload:
            user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Delete ALL sessions for this user
    result = await db.sessions.delete_many({"user_id": user_id})

    response.delete_cookie(key="session_token", path="/")

    await audit_logger.log_action(
        action=AuditAction.LOGOUT,
        user_id=user_id,
        user_email="all-devices",
        details={"sessions_cleared": result.deleted_count},
        status="success"
    )

    return {"message": f"Logged out from all devices. {result.deleted_count} sessions cleared."}

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ===== USER ROUTES =====
@api_router.patch("/users/me", response_model=User)
async def update_profile(update_data: UserUpdate, current_user: User = Depends(get_current_user)):
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict:
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": update_dict}
        )
    
    updated_user = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    return User(**{k: v for k, v in updated_user.items() if k != 'password'})

# ===== DASHBOARD STATS =====
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    from services.cache_service import cache, TTL_DASHBOARD_STATS
    cache_key = f"dashboard:stats:{current_user.id}:{current_user.role}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    if current_user.role == UserRole.ADMIN:
        total_orders = await db.orders.count_documents({})
        total_users = await db.users.count_documents({"role": "ecommerce"})
        total_products = await db.products.count_documents({})
        in_transit = await db.orders.count_documents({"status": OrderStatus.IN_TRANSIT})
    elif current_user.role == UserRole.ECOMMERCE:
        total_orders = await db.orders.count_documents({"user_id": current_user.id})
        total_products = await db.products.count_documents({"user_id": current_user.id})
        total_users = 0
        in_transit = await db.orders.count_documents({"user_id": current_user.id, "status": OrderStatus.IN_TRANSIT})
    else:  # DELIVERY
        assigned_orders = await db.orders.count_documents({"delivery_partner": current_user.id})
        in_transit = await db.orders.count_documents({"delivery_partner": current_user.id, "status": OrderStatus.IN_TRANSIT})
        total_orders = assigned_orders
        total_users = 0
        total_products = 0
    
    result = {
        "total_orders": total_orders,
        "total_users": total_users,
        "total_products": total_products,
        "in_transit": in_transit
    }
    cache.set(cache_key, result, TTL_DASHBOARD_STATS)
    return result

@api_router.get("/dashboard/orders-by-status")
async def get_orders_by_status(current_user: User = Depends(get_current_user)):
    """Get order count grouped by status for charts"""
    from services.cache_service import cache, TTL_ORDERS_BY_STATUS
    cache_key = f"dashboard:orders_status:{current_user.id}:{current_user.role}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    pipeline = []
    
    # Filter by user role
    if current_user.role == UserRole.ECOMMERCE:
        pipeline.append({"$match": {"user_id": current_user.id}})
    elif current_user.role == UserRole.DELIVERY:
        pipeline.append({"$match": {"delivery_partner": current_user.id}})
    
    # Group by status
    pipeline.extend([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ])
    
    result = await db.orders.aggregate(pipeline).to_list(length=None)
    
    # Format response with French labels
    status_labels = {
        "in_stock": "En stock",
        "preparing": "Préparation",
        "ready_to_ship": "Prêt",
        "in_transit": "En transit",
        "delivered": "Livré",
        "returned": "Retourné"
    }
    
    data = [
        {"name": status_labels.get(item["_id"], item["_id"]), "value": item["count"]}
        for item in result
    ]
    cache.set(cache_key, data, TTL_ORDERS_BY_STATUS)
    return data

@api_router.get("/dashboard/revenue-evolution")
async def get_revenue_evolution(current_user: User = Depends(get_current_user)):
    """Get revenue evolution over the last 7 days"""
    # Calculate date range (last 7 days)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = today - timedelta(days=6)
    
    pipeline = []
    
    # Filter by user role and date range
    match_stage = {"created_at": {"$gte": seven_days_ago.isoformat()}}
    if current_user.role == UserRole.ECOMMERCE:
        match_stage["user_id"] = current_user.id
    elif current_user.role == UserRole.DELIVERY:
        match_stage["delivery_partner"] = current_user.id
    
    pipeline.append({"$match": match_stage})
    
    # Parse created_at and group by date
    pipeline.extend([
        {
            "$addFields": {
                "date": {
                    "$dateFromString": {
                        "dateString": "$created_at",
                        "onError": None,
                        "onNull": None
                    }
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$date"
                    }
                },
                "revenue": {"$sum": "$cod_amount"}
            }
        },
        {"$sort": {"_id": 1}}
    ])
    
    result = await db.orders.aggregate(pipeline).to_list(length=None)
    
    # Create a map of dates to revenue
    revenue_map = {item["_id"]: item["revenue"] for item in result if item["_id"]}
    
    # Generate all 7 days with French day names
    day_names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    response = []
    
    for i in range(7):
        date = seven_days_ago + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        day_of_week = date.weekday()  # 0=Monday, 6=Sunday
        
        response.append({
            "name": day_names[day_of_week],
            "date": date_str,
            "revenus": revenue_map.get(date_str, 0)
        })
    
    return response

@api_router.get("/dashboard/top-wilayas")
async def get_top_wilayas(current_user: User = Depends(get_current_user)):
    """Get top 5 wilayas by order count"""
    pipeline = []
    
    # Filter by user role
    if current_user.role == UserRole.ECOMMERCE:
        pipeline.append({"$match": {"user_id": current_user.id}})
    elif current_user.role == UserRole.DELIVERY:
        pipeline.append({"$match": {"delivery_partner": current_user.id}})
    
    # Group by wilaya
    pipeline.extend([
        {"$group": {"_id": "$recipient.wilaya", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ])
    
    result = await db.orders.aggregate(pipeline).to_list(length=None)
    
    return [
        {"name": item["_id"] if item["_id"] else "Non spécifié", "value": item["count"]}
        for item in result
    ]

# ===== ORDER ROUTES =====
@api_router.post("/orders", response_model=Order)
async def create_order(
    order_data: OrderCreate, 
    send_whatsapp_confirmation: bool = False,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """
    Create a new order with detailed validation and error messages
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.ECOMMERCE]:
        raise HTTPException(status_code=403, detail="Non autorisé: Seuls les administrateurs et e-commerçants peuvent créer des commandes")
    
    # Detailed validation with specific error messages
    if not order_data.recipient.name or not order_data.recipient.name.strip():
        raise HTTPException(status_code=400, detail="Champ requis manquant: 'Nom du destinataire' (recipient.name)")
    
    if not order_data.recipient.phone or not order_data.recipient.phone.strip():
        raise HTTPException(status_code=400, detail="Champ requis manquant: 'Téléphone du destinataire' (recipient.phone)")
    
    if not order_data.recipient.wilaya or not order_data.recipient.wilaya.strip():
        raise HTTPException(status_code=400, detail="Champ requis manquant: 'Wilaya' (recipient.wilaya)")
    
    if order_data.cod_amount is None or order_data.cod_amount < 0:
        raise HTTPException(status_code=400, detail="Montant COD invalide: Doit être un nombre positif")
    
    # Generate tracking ID
    tracking_id = f"BEX-{secrets.token_hex(6).upper()}"
    
    # Generate unique PIN code (4 digits)
    import random
    pin_code = str(random.randint(1000, 9999))
    
    # Get organization info for sender
    org = await db.organizations.find_one({}, {"_id": 0})
    if not org:
        org = Organization().model_dump()
        org['created_at'] = org['created_at'].isoformat()
        await db.organizations.insert_one(org)
    
    sender_info = AddressInfo(
        name=org['name'],
        phone=org['phone'],
        address=org['address'],
        wilaya="Batna",
        commune="Batna"
    )
    
    # AUTO-CALCULATE SHIPPING COST from Pricing Table
    shipping_cost = 0.0
    try:
        # Normalize delivery type
        delivery_type_normalized = "home" if "domicile" in order_data.delivery_type.lower() else "desk"
        
        # Query pricing table
        pricing = await db.pricing_table.find_one({
            "wilaya": order_data.recipient.wilaya,
            "delivery_type": delivery_type_normalized
        }, {"_id": 0})
        
        if pricing:
            shipping_cost = pricing.get("price", 0.0)
            logger.info(f"✅ Shipping cost auto-calculated: {shipping_cost} DZD for {order_data.recipient.wilaya} - {delivery_type_normalized}")
        else:
            logger.warning(f"⚠️ No pricing found for {order_data.recipient.wilaya} - {delivery_type_normalized}, using 0.0")
    except Exception as e:
        logger.error(f"❌ Error calculating shipping cost: {str(e)}")
    
    # Calculate net to merchant
    net_to_merchant = order_data.cod_amount - shipping_cost
    
    order_obj = Order(
        **order_data.model_dump(),
        tracking_id=tracking_id,
        user_id=current_user.id,
        sender=sender_info,
        pin_code=pin_code,  # Store unique PIN
        shipping_cost=shipping_cost,  # Auto-filled from pricing table
        net_to_merchant=net_to_merchant,  # Auto-calculated
        payment_status="unpaid"  # Default status
    )
    
    order_dict = order_obj.model_dump()
    order_dict['created_at'] = order_dict['created_at'].isoformat()
    order_dict['updated_at'] = order_dict['updated_at'].isoformat()
    if order_dict.get('collected_date'):
        order_dict['collected_date'] = order_dict['collected_date'].isoformat()
    if order_dict.get('transferred_date'):
        order_dict['transferred_date'] = order_dict['transferred_date'].isoformat()
    
    await db.orders.insert_one(order_dict)
    
    # Log order creation
    await audit_logger.log_action(
        action=AuditAction.CREATE_ORDER,
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type="order",
        resource_id=order_obj.id,
        details={
            "tracking_id": tracking_id,
            "recipient_wilaya": order_data.recipient.wilaya,
            "cod_amount": order_data.cod_amount
        },
        ip_address=request.client.host if request and request.client else None,
        status="success"
    )
    
    # Optional: Send WhatsApp confirmation automatically
    if send_whatsapp_confirmation and order_obj.recipient.phone:
        try:
            from services.twilio_service import twilio_service
            twilio_service.send_order_confirmation(
                to_phone=order_obj.recipient.phone,
                order_id=order_obj.id,
                tracking_id=tracking_id,
                customer_name=order_obj.recipient.name,
                items_description=order_obj.description or "Votre commande",
                cod_amount=order_obj.cod_amount
            )
            logger.info(f"✅ WhatsApp confirmation sent for order {order_obj.id}")
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp confirmation: {str(e)}")
            # Don't fail the order creation if WhatsApp fails
    
    return order_obj

@api_router.get("/orders")
async def get_orders(
    status: Optional[OrderStatus] = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """
    Get orders with server-side pagination
    Returns: {orders: [], total: int, page: int, limit: int, pages: int}
    """
    query = {}
    
    if current_user.role == UserRole.ECOMMERCE:
        query["user_id"] = current_user.id
    elif current_user.role == UserRole.DELIVERY:
        query["delivery_partner"] = current_user.id
    
    if status:
        query["status"] = status
    
    # Get total count
    total = await db.orders.count_documents(query)
    
    # Calculate pagination
    skip = (page - 1) * limit
    pages = (total + limit - 1) // limit  # Ceiling division
    
    # Get paginated orders
    orders = await db.orders.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    for order in orders:
        if isinstance(order.get('created_at'), str):
            order['created_at'] = datetime.fromisoformat(order['created_at'])
        if 'updated_at' in order and isinstance(order['updated_at'], str):
            order['updated_at'] = datetime.fromisoformat(order['updated_at'])
        elif 'updated_at' not in order:
            # Set updated_at to created_at if missing
            order['updated_at'] = order.get('created_at', datetime.now(timezone.utc))
    
    return {
        "orders": orders,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }

@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str, current_user: User = Depends(get_current_user)):
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check permissions
    if current_user.role == UserRole.ECOMMERCE and order['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if isinstance(order['created_at'], str):
        order['created_at'] = datetime.fromisoformat(order['created_at'])
    if isinstance(order['updated_at'], str):
        order['updated_at'] = datetime.fromisoformat(order['updated_at'])
    
    return Order(**order)

@api_router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status: OrderStatus,
    current_user: User = Depends(get_current_user)
):
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Status updated"}

@api_router.post("/orders/bordereau")
async def generate_bordereau(order_ids: List[str], current_user: User = Depends(get_current_user)):
    if not order_ids:
        raise HTTPException(status_code=400, detail="No orders selected")
    
    # Get first order for now (single bordereau)
    order = await db.orders.find_one({"id": order_ids[0]}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check permissions
    if current_user.role == UserRole.ECOMMERCE and order['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    pdf_buffer = generate_bordereau_pdf(order)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=bordereau_{order['tracking_id']}.pdf"}
    )


# ===== TRACKING ROUTES =====
@api_router.post("/orders/{order_id}/tracking")
async def add_tracking_event(
    order_id: str,
    event_data: TrackingEventCreate,
    current_user: User = Depends(get_current_user)
):
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    tracking_event = TrackingEvent(**event_data.model_dump(), order_id=order_id)
    tracking_dict = tracking_event.model_dump()
    tracking_dict['timestamp'] = tracking_dict['timestamp'].isoformat()
    
    await db.tracking_events.insert_one(tracking_dict)
    
    # Update order status if provided
    if event_data.status:
        await db.orders.update_one(
            {"id": order_id},
            {"$set": {"status": event_data.status, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"message": "Tracking event added"}

@api_router.get("/orders/{order_id}/tracking")
async def get_tracking_events(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check permissions
    if current_user.role == UserRole.ECOMMERCE and order['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    events = await db.tracking_events.find({"order_id": order_id}, {"_id": 0}).sort("timestamp", -1).to_list(100)
    
    for event in events:
        if isinstance(event['timestamp'], str):
            event['timestamp'] = datetime.fromisoformat(event['timestamp'])
    
    return events

@api_router.get("/orders/filter/by-delivery-partner")
async def filter_orders_by_delivery_partner(
    delivery_partner: str,
    current_user: User = Depends(get_current_user)
):
    query = {"delivery_partner": delivery_partner}
    
    if current_user.role == UserRole.ECOMMERCE:
        query["user_id"] = current_user.id
    
    orders = await db.orders.find(query, {"_id": 0}).to_list(1000)
    
    for order in orders:
        if isinstance(order.get('created_at'), str):
            order['created_at'] = datetime.fromisoformat(order['created_at'])
        if 'updated_at' in order and isinstance(order['updated_at'], str):
            order['updated_at'] = datetime.fromisoformat(order['updated_at'])
        elif 'updated_at' not in order:
            # Set updated_at to created_at if missing
            order['updated_at'] = order.get('created_at', datetime.now(timezone.utc))
    
    return orders

@api_router.get("/orders/filter/by-user")
async def filter_orders_by_user(
    user_id: str,
    current_user: User = Depends(get_current_admin)
):
    orders = await db.orders.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    for order in orders:
        if isinstance(order.get('created_at'), str):
            order['created_at'] = datetime.fromisoformat(order['created_at'])
        if 'updated_at' in order and isinstance(order['updated_at'], str):
            order['updated_at'] = datetime.fromisoformat(order['updated_at'])
        elif 'updated_at' not in order:
            # Set updated_at to created_at if missing
            order['updated_at'] = order.get('created_at', datetime.now(timezone.utc))
    
    return orders

@api_router.get("/users/ecommerce")
async def get_ecommerce_users(current_user: User = Depends(get_current_admin)):
    users = await db.users.find({"role": "ecommerce"}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@api_router.get("/users")
async def get_all_users(current_user: User = Depends(get_current_admin)):
    """Get all users (admin only) - used for driver management"""
    try:
        users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
        # ALWAYS return empty array if no users, NEVER error
        if not users:
            users = []
        return {"users": users}
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        # Return empty array instead of 500 error
        return {"users": []}


# ===== PRODUCT ROUTES =====
@api_router.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN, UserRole.ECOMMERCE]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if SKU exists
    existing = await db.products.find_one({"sku": product_data.sku, "user_id": current_user.id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    product_obj = Product(**product_data.model_dump(), user_id=current_user.id)
    product_dict = product_obj.model_dump()
    product_dict['created_at'] = product_dict['created_at'].isoformat()
    
    await db.products.insert_one(product_dict)
    
    return product_obj

@api_router.get("/products", response_model=List[Product])
async def get_products(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.ECOMMERCE:
        query = {"user_id": current_user.id}
    else:
        query = {}
    
    products = await db.products.find(query, {"_id": 0}).to_list(1000)
    
    for product in products:
        if isinstance(product['created_at'], str):
            product['created_at'] = datetime.fromisoformat(product['created_at'])
    
    return products

@api_router.patch("/products/{product_id}/stock")
async def update_product_stock(
    product_id: str,
    stock_available: int,
    current_user: User = Depends(get_current_user)
):
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if current_user.role == UserRole.ECOMMERCE and product['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.products.update_one(
        {"id": product_id},
        {"$set": {"stock_available": stock_available}}
    )
    
    return {"message": "Stock updated"}

# ===== DELIVERY PARTNER ROUTES (ADMIN ONLY) =====
@api_router.post("/delivery-partners", response_model=DeliveryPartner)
async def create_delivery_partner(
    partner_data: DeliveryPartnerCreate,
    current_user: User = Depends(get_current_admin)
):
    partner_obj = DeliveryPartner(**partner_data.model_dump())
    partner_dict = partner_obj.model_dump()
    partner_dict['created_at'] = partner_dict['created_at'].isoformat()
    
    await db.delivery_partners.insert_one(partner_dict)
    
    return partner_obj

@api_router.get("/delivery-partners", response_model=List[DeliveryPartner])
async def get_delivery_partners(current_user: User = Depends(get_current_admin)):
    partners = await db.delivery_partners.find({}, {"_id": 0}).to_list(100)
    
    for partner in partners:
        if isinstance(partner['created_at'], str):
            partner['created_at'] = datetime.fromisoformat(partner['created_at'])
    
    return partners

# ===== CUSTOMER ROUTES =====
@api_router.post("/customers", response_model=Customer)
async def create_customer(
    customer_data: CustomerCreate,
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.ECOMMERCE]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Generate unique customer ID
    count = await db.customers.count_documents({})
    customer_id = f"BEX-CUST-{str(count + 1).zfill(4)}"
    
    customer_obj = Customer(**customer_data.model_dump(), user_id=current_user.id, customer_id=customer_id)
    customer_dict = customer_obj.model_dump()
    customer_dict['created_at'] = customer_dict['created_at'].isoformat()
    
    await db.customers.insert_one(customer_dict)
    
    return customer_obj

@api_router.get("/customers", response_model=List[Customer])
async def get_customers(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.ECOMMERCE:
        query = {"user_id": current_user.id}
    else:
        query = {}
    
    customers = await db.customers.find(query, {"_id": 0}).to_list(1000)
    
    for customer in customers:
        if isinstance(customer['created_at'], str):
            customer['created_at'] = datetime.fromisoformat(customer['created_at'])
    
    return customers


@api_router.post("/upload-profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename
    import uuid
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / "profile_pictures" / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Return URL
    file_url = f"/uploads/profile_pictures/{unique_filename}"
    return {"url": file_url}

@api_router.post("/customers/{customer_id}/generate-qr")
async def generate_customer_qr(
    customer_id: str,
    current_user: User = Depends(get_current_user)
):
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Generate QR code data
    qr_data = f"BeyondExpress|{customer['customer_id']}|{customer['name']}|{customer['phone']}"
    
    # Update customer with QR code data
    await db.customers.update_one(
        {"id": customer_id},
        {"$set": {"qr_code_data": qr_data}}
    )
    
    # Generate QR code image
    from pdf_generator_yalidine import generate_qr_code
    qr_buffer = generate_qr_code(qr_data)
    
    return StreamingResponse(
        qr_buffer,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=qr_{customer['customer_id']}.png"}
    )

@api_router.patch("/customers/{customer_id}")
async def update_customer(
    customer_id: str,
    update_data: dict,
    current_user: User = Depends(get_current_user)
):
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if current_user.role == UserRole.ECOMMERCE and customer['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.customers.update_one(
        {"id": customer_id},
        {"$set": update_data}
    )
    
    return {"message": "Customer updated"}

# ===== INVOICE ROUTES =====
@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.ECOMMERCE:
        query = {"user_id": current_user.id}
    else:
        query = {}
    
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(1000)
    
    for invoice in invoices:
        if isinstance(invoice['created_at'], str):
            invoice['created_at'] = datetime.fromisoformat(invoice['created_at'])
        if invoice.get('due_date') and isinstance(invoice['due_date'], str):
            invoice['due_date'] = datetime.fromisoformat(invoice['due_date'])
        if invoice.get('paid_at') and isinstance(invoice['paid_at'], str):
            invoice['paid_at'] = datetime.fromisoformat(invoice['paid_at'])
    
    return invoices

# ===== AI CHAT ROUTES =====
@api_router.post("/ai-chat")
async def ai_chat(
    message: str,
    model: str = "gpt-4o",
    provider: str = "openai",
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Get or create chat session
    chat_session = await db.chat_sessions.find_one({
        "user_id": current_user.id,
        "session_id": session_id
    }, {"_id": 0})
    
    if not chat_session:
        chat_session = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "session_id": session_id,
            "model": model,
            "provider": provider,
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.chat_sessions.insert_one(chat_session)
    
    # Initialize LLM chat
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    system_message = f"""You are an AI assistant for Beyond Express, a 3PL logistics platform. 
User role: {current_user.role}
User name: {current_user.name}
You can help with:
- Order status queries (format: BEX-XXXXXX)
- Stock information
- Creating shipments
- Generating shipping labels
- General logistics questions

Answer in the user's preferred language: {current_user.language}"""
    
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message=system_message
    ).with_model(provider, model)
    
    user_message = UserMessage(text=message)
    response = await chat.send_message(user_message)
    
    # Save messages
    chat_session['messages'].append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    chat_session['messages'].append({
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    await db.chat_sessions.update_one(
        {"user_id": current_user.id, "session_id": session_id},
        {"$set": {"messages": chat_session['messages']}}
    )
    
    return {
        "response": response,
        "session_id": session_id
    }

@api_router.get("/ai-chat/history")
async def get_chat_history(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    query = {"user_id": current_user.id}
    if session_id:
        query["session_id"] = session_id
    
    sessions = await db.chat_sessions.find(query, {"_id": 0}).sort("created_at", -1).to_list(10)
    
    return sessions

# ===== ORGANIZATION ROUTES (ADMIN ONLY) =====
@api_router.get("/organization", response_model=Organization)
async def get_organization():
    org = await db.organizations.find_one({}, {"_id": 0})
    if not org:
        org_obj = Organization()
        org_dict = org_obj.model_dump()
        org_dict['created_at'] = org_dict['created_at'].isoformat()
        await db.organizations.insert_one(org_dict)
        return org_obj
    
    if isinstance(org['created_at'], str):
        org['created_at'] = datetime.fromisoformat(org['created_at'])
    
    return Organization(**org)

@api_router.patch("/organization")
async def update_organization(
    update_data: OrganizationBase,
    current_user: User = Depends(get_current_admin)
):
    org = await db.organizations.find_one({}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    await db.organizations.update_one(
        {"id": org['id']},
        {"$set": update_data.model_dump()}
    )
    
    return {"message": "Organization updated"}

# ===== API KEY ROUTES =====
@api_router.post("/api-keys")
async def create_api_key(
    name: str,
    current_user: User = Depends(get_current_user)
):
    api_key = f"bex_{secrets.token_urlsafe(32)}"
    
    api_key_obj = APIKey(
        user_id=current_user.id,
        key=api_key,
        name=name
    )
    
    api_key_dict = api_key_obj.model_dump()
    api_key_dict['created_at'] = api_key_dict['created_at'].isoformat()
    
    await db.api_keys.insert_one(api_key_dict)
    
    return {"api_key": api_key, "name": name}

@api_router.get("/api-keys", response_model=List[APIKey])
async def get_api_keys(current_user: User = Depends(get_current_user)):
    keys = await db.api_keys.find({"user_id": current_user.id}, {"_id": 0}).to_list(100)
    
    for key in keys:
        if isinstance(key['created_at'], str):
            key['created_at'] = datetime.fromisoformat(key['created_at'])
    
    return keys

# ===== SUPPORT ROUTES =====
@api_router.post("/support/tickets", response_model=SupportTicket)
async def create_support_ticket(
    ticket_data: SupportTicketCreate,
    current_user: User = Depends(get_current_user)
):
    ticket_obj = SupportTicket(**ticket_data.model_dump(), user_id=current_user.id)
    ticket_dict = ticket_obj.model_dump()
    ticket_dict['created_at'] = ticket_dict['created_at'].isoformat()
    
    await db.support_tickets.insert_one(ticket_dict)
    
    return ticket_obj

@api_router.get("/support/tickets", response_model=List[SupportTicket])
async def get_support_tickets(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.ADMIN:
        query = {}
    else:
        query = {"user_id": current_user.id}
    
    tickets = await db.support_tickets.find(query, {"_id": 0}).to_list(100)
    
    for ticket in tickets:
        if isinstance(ticket['created_at'], str):
            ticket['created_at'] = datetime.fromisoformat(ticket['created_at'])
    
    return tickets


# ===== PUBLIC TRACKING ENDPOINT (NO AUTH REQUIRED) =====
@api_router.get("/public/track/{tracking_id}")
async def public_track_order(tracking_id: str):
    """
    Public tracking endpoint - NO AUTHENTICATION REQUIRED
    Returns only non-sensitive tracking information for customers
    """
    try:
        # Find order by tracking_id
        order = await db.orders.find_one({"tracking_id": tracking_id}, {"_id": 0})
        
        if not order:
            raise HTTPException(status_code=404, detail="Numéro de suivi introuvable")
        
        # Get tracking events history
        events = await db.tracking_events.find(
            {"order_id": order.get("id")}, 
            {"_id": 0}
        ).sort("timestamp", 1).to_list(100)  # Sort chronologically (oldest first)
        
        # Return ONLY non-sensitive information
        public_data = {
            "tracking_id": order.get("tracking_id"),
            "status": order.get("status"),
            "recipient_wilaya": order.get("recipient", {}).get("wilaya"),
            "recipient_commune": order.get("recipient", {}).get("commune"),
            "created_at": order.get("created_at"),
            "delivery_partner": order.get("delivery_partner"),
            "delivery_type": order.get("delivery_type"),
            "events": [
                {
                    "status": event.get("status"),
                    "timestamp": event.get("timestamp"),
                    "location": event.get("location"),
                    "notes": event.get("notes")
                }
                for event in events
            ]
        }
        
        return public_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in public tracking: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des données")

# ===== AUDIT LOG ROUTES (ADMIN ONLY) =====
@api_router.get("/audit/logs")
async def get_audit_logs(
    limit: int = 100,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_admin)
):
    """Get recent audit logs (admin only)"""
    if action or user_id:
        logs = await audit_logger.search_logs(
            action=action,
            user_id=user_id,
            limit=limit
        )
    else:
        logs = await audit_logger.get_recent_logs(limit=limit)
    
    return {"logs": logs, "total": len(logs)}

@api_router.get("/audit/verify-integrity")
async def verify_audit_integrity(current_user: User = Depends(get_current_admin)):
    """Verify the integrity of the audit log chain"""
    result = await audit_logger.verify_chain_integrity()
    return result

@api_router.get("/audit/user/{user_id}")
async def get_user_audit_logs(
    user_id: str,
    limit: int = 100,
    current_user: User = Depends(get_current_admin)
):
    """Get all audit logs for a specific user"""
    logs = await audit_logger.get_user_actions(user_id, limit=limit)
    return {"user_id": user_id, "logs": logs, "total": len(logs)}

# Include the router in the main app
app.include_router(api_router)

# Include WhatsApp routes
app.include_router(whatsapp_router.router, prefix="/api/whatsapp", tags=["whatsapp"])

# Include Subscriptions routes
app.include_router(subscriptions_router.router, prefix="/api/subscriptions", tags=["subscriptions"])

# Include AI Assistant routes
# Inject the get_current_user dependency
ai_assistant_router.get_current_user_dependency = get_current_user
app.include_router(ai_assistant_router.router, prefix="/api/ai", tags=["ai"])

# Include Carriers routes
carriers_router.get_current_user_dependency = get_current_user
app.include_router(carriers_router.router, prefix="/api/carriers", tags=["carriers"])

# Include Financial Management routes (COD Reconciliation)
from routes import financial as financial_router
financial_router.get_current_user_dependency = get_current_user
app.include_router(financial_router.router, prefix="/api/financial", tags=["financial"])

# Include Pricing Table routes
from routes import pricing as pricing_router
pricing_router.get_current_user_dependency = get_current_user
app.include_router(pricing_router.router, prefix="/api/pricing", tags=["pricing"])

# Include Bulk Import routes
from routes import bulk_import as bulk_import_router
app.include_router(bulk_import_router.router, prefix="/api/bulk", tags=["bulk_import"])

# Include Labels routes
from routes import labels as labels_router
app.include_router(labels_router.router, prefix="/api/orders", tags=["labels"])

# Include Driver API routes
from routes import driver as driver_router
app.include_router(driver_router.router, prefix="/api/driver", tags=["driver"])

# Include Notifications routes
from routes import notifications as notifications_router
app.include_router(
    notifications_router.router, 
    prefix="/api/notifications", 
    tags=["notifications"]
)

# Include AI Config routes
from routes import ai_config as ai_config_router
app.include_router(ai_config_router.router, prefix="/api/ai-config", tags=["ai_config"])

# Include Enhanced Chat routes
from routes import enhanced_chat as enhanced_chat_router
app.include_router(enhanced_chat_router.router, prefix="/api/chat", tags=["chat"])

# Include Returns/RMA routes
from routes import returns as returns_router
app.include_router(returns_router.router, prefix="/api/returns", tags=["returns"])

# Include WhatsApp Meta Cloud API routes (Zero Cost)
from routes import whatsapp_meta as whatsapp_meta_router
app.include_router(whatsapp_meta_router.router, prefix="/api/whatsapp-meta", tags=["whatsapp_meta"])

# Include Smart Circuit Routing routes
from routes import smart_routing as smart_routing_router
app.include_router(smart_routing_router.router, prefix="/api/routing", tags=["routing"])

# Include Warehouse routes
from routes import warehouse as warehouse_router
app.include_router(warehouse_router.router, prefix="/api/warehouse", tags=["warehouse"])

# Include AI Brain routes
from routes import ai_brain as ai_brain_router
app.include_router(ai_brain_router.router, prefix="/api/ai-brain", tags=["ai-brain"])

# Include Shipping routes (Smart Router)
app.include_router(shipping_router.router, prefix="/api/shipping", tags=["shipping"])

# Include Webhooks routes (Carrier notifications)
app.include_router(webhooks_router.router, prefix="/api/webhooks", tags=["webhooks"])


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.on_event("startup")
async def startup_performance():
    """Create MongoDB indexes and verify Redis cache on startup."""
    from services.index_manager import ensure_indexes
    from services.cache_service import cache
    idx = await ensure_indexes(db)
    logger.info(f"Startup: indexes={idx}, redis={cache.is_available}")