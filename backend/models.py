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

class CarrierType(str, Enum):
    YALIDINE = "yalidine"
    DHD = "dhd"
    ZR_EXPRESS = "zr_express"
    MAYSTRO = "maystro"
    NORD_OUEST = "nord_ouest"
    GUEPEX = "guepex"
    SONIC = "sonic"
    PROCOLIS = "procolis"
    SPEEDAF = "speedaf"
    PICK_UP = "pick_up"
    ECHO_FREIGHT = "echo_freight"
    SHL = "shl"
    COLIPOSTE = "coliposte"

class CarrierStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"

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

class PaymentStatus(str, Enum):
    """Financial status for COD reconciliation"""
    UNPAID = "unpaid"  # Order created, payment not collected
    COLLECTED_BY_DRIVER = "collected_by_driver"  # Driver collected cash from customer
    TRANSFERRED_TO_MERCHANT = "transferred_to_merchant"  # Money transferred to merchant
    RETURNED = "returned"  # Order returned, no payment

class DeliveryType(str, Enum):
    """Type de livraison pour pricing"""
    HOME = "home"  # Livraison à domicile
    DESK = "desk"  # Livraison en bureau (stop desk)

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
    
    # Carrier Integration fields
    carrier_type: Optional[str] = None  # yalidine, zr_express, etc.
    carrier_tracking_id: Optional[str] = None  # Carrier's tracking number
    carrier_synced_at: Optional[str] = None  # Last sync timestamp
    carrier_label_url: Optional[str] = None  # PDF label URL
    smart_routed: bool = False  # Was this order routed by AI?
    routing_reason: Optional[str] = None  # Why this carrier was selected
    last_sync_at: Optional[str] = None  # Last tracking status sync
    last_carrier_status: Optional[str] = None  # Raw status from carrier
    
    # Financial fields for COD Reconciliation
    shipping_cost: float = 0.0  # Frais de livraison (auto-filled from PricingTable)
    net_to_merchant: float = 0.0  # Net à payer au vendeur (cod_amount - shipping_cost)
    payment_status: PaymentStatus = PaymentStatus.UNPAID  # Statut financier
    collected_date: Optional[datetime] = None  # Date d'encaissement
    transferred_date: Optional[datetime] = None  # Date de virement au marchand
    
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


# ===== CARRIER INTEGRATION MODELS =====

class CarrierCredentials(BaseModel):
    """Encrypted credentials for a carrier API"""
    api_key: Optional[str] = None
    api_token: Optional[str] = None
    user_id: Optional[str] = None
    api_secret: Optional[str] = None
    center_id: Optional[str] = None
    # Additional fields as needed per carrier

class CarrierConfigBase(BaseModel):
    """Carrier API configuration for a user"""
    user_id: str
    carrier_type: CarrierType
    carrier_name: str
    is_active: bool = False
    credentials: CarrierCredentials
    test_mode: bool = True  # Sandbox vs Production
    last_test_status: Optional[CarrierStatus] = None
    last_test_at: Optional[datetime] = None
    last_test_message: Optional[str] = None

class CarrierConfig(CarrierConfigBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CarrierConfigCreate(BaseModel):
    carrier_type: CarrierType
    credentials: CarrierCredentials
    test_mode: bool = True

class CarrierConfigUpdate(BaseModel):
    credentials: Optional[CarrierCredentials] = None
    is_active: Optional[bool] = None
    test_mode: Optional[bool] = None

class TestConnectionRequest(BaseModel):
    carrier_type: CarrierType
    credentials: CarrierCredentials
    test_mode: bool = True

class TestConnectionResponse(BaseModel):
    success: bool
    status: CarrierStatus


# ===== PRICING TABLE MODELS (COD Reconciliation) =====

class PricingTableBase(BaseModel):
    """Pricing table for automatic shipping cost calculation"""
    wilaya: str  # Wilaya name (e.g., "Alger", "Batna")
    delivery_type: DeliveryType  # HOME or DESK
    price: float  # Shipping cost in DZD

class PricingTableCreate(PricingTableBase):
    pass

class PricingTable(PricingTableBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BatchPaymentUpdate(BaseModel):
    """Batch update payment status for multiple orders"""
    order_ids: List[str]
    new_status: PaymentStatus
    notes: Optional[str] = None

