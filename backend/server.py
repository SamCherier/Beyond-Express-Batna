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
from routes import whatsapp as whatsapp_router
from routes import subscriptions as subscriptions_router
from routes import ai_assistant as ai_assistant_router
from routes import carriers as carriers_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')


# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
async def register(user_data: UserCreate):
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
    
    return user_obj

@api_router.post("/auth/login")
async def login(credentials: UserLogin, response: Response):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user_doc['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user_doc['id']})
    
    # Create session
    session_token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_doc['id'],
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sessions.insert_one(session_doc)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=7 * 24 * 60 * 60,
        path="/",
        httponly=True,
        samesite="lax",
        secure=False
    )
    
    user_obj = User(**{k: v for k, v in user_doc.items() if k != 'password'})
    
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
    
    # Create session
    session_token = session_data['session_token']
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_doc['id'],
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sessions.insert_one(session_doc)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=7 * 24 * 60 * 60,
        path="/",
        httponly=True,
        samesite="lax",
        secure=False
    )
    
    user_obj = User(**{k: v for k, v in user_doc.items() if k != 'password'})
    
    return {
        "user": user_obj,
        "session_token": session_token
    }

@api_router.post("/auth/logout")
async def logout(response: Response, session_token: Optional[str] = Cookie(None)):
    if session_token:
        await db.sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out successfully"}

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
    
    return {
        "total_orders": total_orders,
        "total_users": total_users,
        "total_products": total_products,
        "in_transit": in_transit
    }

@api_router.get("/dashboard/orders-by-status")
async def get_orders_by_status(current_user: User = Depends(get_current_user)):
    """Get order count grouped by status for charts"""
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
    
    return [
        {"name": status_labels.get(item["_id"], item["_id"]), "value": item["count"]}
        for item in result
    ]

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
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.ECOMMERCE]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
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
    
    order_obj = Order(
        **order_data.model_dump(),
        tracking_id=tracking_id,
        user_id=current_user.id,
        sender=sender_info,
        pin_code=pin_code  # Store unique PIN
    )
    
    order_dict = order_obj.model_dump()
    order_dict['created_at'] = order_dict['created_at'].isoformat()
    order_dict['updated_at'] = order_dict['updated_at'].isoformat()
    
    await db.orders.insert_one(order_dict)
    
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

@api_router.get("/orders", response_model=List[Order])
async def get_orders(
    status: Optional[OrderStatus] = None,
    current_user: User = Depends(get_current_user)
):
    query = {}
    
    if current_user.role == UserRole.ECOMMERCE:
        query["user_id"] = current_user.id
    elif current_user.role == UserRole.DELIVERY:
        query["delivery_partner"] = current_user.id
    
    if status:
        query["status"] = status
    
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