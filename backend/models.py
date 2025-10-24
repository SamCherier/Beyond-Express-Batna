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
    customer_id: str  # BEX-CUST-XXX
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
