from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    ECOMMERCE = "ecommerce"
    DELIVERY = "delivery"

class OrderStatus(str, Enum):
    IN_STOCK = "in_stock"
    PREPARING = "preparing"
    READY_TO_SHIP = "ready_to_ship"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"
    FAILED = "failed"
    ARCHIVED = "archived"

class Language(str, Enum):
    FR = "fr"
    AR = "ar"
    EN = "en"

class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"

class PlanType(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"

class BillingPeriod(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"  # 3 months
    BIANNUAL = "biannual"    # 6 months
    ANNUAL = "annual"        # 12 months

# User Models
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole
    picture: Optional[str] = None
    language: Language = Language.FR
    theme: Theme = Theme.LIGHT

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: UserRole

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    current_plan: PlanType = PlanType.FREE  # Default to FREE plan
    plan_expires_at: Optional[datetime] = None
    subscription_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[Language] = None
    theme: Optional[Theme] = None
    picture: Optional[str] = None

# Session Models
class Session(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Organization Models
class OrganizationBase(BaseModel):
    name: str = "Beyond Express"
    logo: str = "/logo.png"
    slogan: str = "خليك مركز على البيع… وخلي الباقي علينا !"
    address: str = "City 84 centre-ville Batna, Batna, Algeria"
    email: str = "contact@beyondexpress.com"
    phone: str = "+213 xxx xxx xxx"
    website: str = "beyond.express.dz"

class Organization(OrganizationBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Product Models
class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    price: float
    weight: Optional[float] = None
    category: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    stock_available: int = 0
    stock_reserved: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Order Models
class AddressInfo(BaseModel):
    name: str
    phone: str
    address: str
    wilaya: str
    commune: str

class OrderBase(BaseModel):
    recipient: AddressInfo
    cod_amount: float
    description: str
    service_type: str = "E-COMMERCE"
    delivery_partner: Optional[str] = None
    delivery_type: str = "Livraison à Domicile"  # New field

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tracking_id: str
    user_id: str
    status: OrderStatus = OrderStatus.IN_STOCK
    sender: AddressInfo
    qr_code: Optional[str] = None
    pin_code: str = ""  # New field for unique PIN
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Warehouse Models
class WarehouseBase(BaseModel):
    name: str
    location: str
    capacity: Optional[int] = None

class WarehouseCreate(WarehouseBase):
    pass

class Warehouse(WarehouseBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Delivery Partner Models
class DeliveryPartnerBase(BaseModel):
    name: str
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    active: bool = True
    supported_wilayas: Optional[List[str]] = None
    base_cost: Optional[float] = None

class DeliveryPartnerCreate(DeliveryPartnerBase):
    pass

class DeliveryPartner(DeliveryPartnerBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Customer Models
class CustomerBase(BaseModel):
    name: str
    phone: str
    phone2: Optional[str] = None
    address: str
    wilaya: str
    commune: str
    notes: Optional[str] = None
    profile_picture: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: Optional[str] = None  # BEX-CUST-XXX
    user_id: str
    order_count: int = 0
    qr_code_data: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Invoice Models
class InvoiceBase(BaseModel):
    amount: float
    description: str
    due_date: Optional[datetime] = None

class InvoiceCreate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    invoice_number: str
    paid: bool = False
    paid_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Chat Models
class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    model: str = "gpt-4o"
    provider: str = "openai"
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Support Ticket Models
class SupportTicketBase(BaseModel):
    subject: str
    message: str

class SupportTicketCreate(SupportTicketBase):
    pass

class SupportTicket(SupportTicketBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    status: str = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Tracking Event Models
class TrackingEventBase(BaseModel):
    status: str
    location: Optional[str] = None
    notes: Optional[str] = None

class TrackingEventCreate(TrackingEventBase):
    pass

class TrackingEvent(TrackingEventBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# API Key Model
class APIKey(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    key: str
    name: str
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ===== WHATSAPP MODELS =====

class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class MessageStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    RECEIVED = "received"

class ConversationStatus(str, Enum):
    AI_HANDLING = "ai_handling"
    HUMAN_HANDLING = "human_handling"
    CLOSED = "closed"
    WAITING = "waiting"

class WhatsAppMessageBase(BaseModel):
    message_sid: str
    sender_phone: str
    recipient_phone: str
    body: str
    direction: MessageDirection
    status: MessageStatus = MessageStatus.QUEUED
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WhatsAppMessage(WhatsAppMessageBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConversationBase(BaseModel):
    customer_phone: str
    customer_name: Optional[str] = None
    status: ConversationStatus = ConversationStatus.AI_HANDLING
    assigned_agent: Optional[str] = None
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    message_count: int = 0
    unread_count: int = 0

class Conversation(ConversationBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ===== SUBSCRIPTION & PLAN MODELS =====

class PlanFeatures(BaseModel):
    """Features and limits for each plan"""
    # Core limits
    max_orders_per_month: int
    max_delivery_companies: int
    max_connected_pages: int = 1
    max_stock_items: Optional[int] = None
    
    # Included services
    preparations_included: int = 0
    pickups_per_week: int = 0
    
    # Features (boolean flags)
    stock_management: bool = False
    whatsapp_auto_confirmation: bool = False
    ai_content_generator: bool = False
    ai_generator_uses: int = 0
    advanced_analytics: bool = False
    pro_dashboard: bool = False
    unlimited_delivery_companies: bool = False
    package_tracking: bool = False
    detailed_reports: bool = False
    dedicated_account_manager: bool = False
    preferred_partner_rates: bool = False
    daily_pickup: bool = False

class PlanPricing(BaseModel):
    """Pricing information for a plan"""
    monthly_price: float
    quarterly_price: Optional[float] = None
    biannual_price: Optional[float] = None
    annual_price: Optional[float] = None
    onboarding_fee: Optional[float] = None
    currency: str = "DZD"

class Plan(BaseModel):
    """Subscription plan/pack"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_type: PlanType
    name_fr: str
    name_ar: str
    name_en: str
    description_fr: str
    description_ar: str
    description_en: str
    target_audience_fr: str
    target_audience_ar: str
    features: PlanFeatures
    pricing: PlanPricing
    is_active: bool = True
    display_order: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SubscriptionBase(BaseModel):
    """User subscription to a plan"""
    user_id: str
    plan_id: str
    plan_type: PlanType
    billing_period: BillingPeriod
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    start_date: datetime
    end_date: datetime
    amount_paid: float = 0.0
    payment_method: Optional[str] = None

class Subscription(SubscriptionBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    auto_renew: bool = False
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SendWhatsAppMessageRequest(BaseModel):
    to_phone: str = Field(..., description="Recipient WhatsApp phone number in E.164 format")
    message_body: str = Field(..., description="Message text content")
    order_id: Optional[str] = None

class AIContext(BaseModel):
    conversation_id: str
    customer_phone: str
    last_intent: Optional[str] = None
    order_references: List[str] = Field(default_factory=list)
    language: Language = Language.FR
    context_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

