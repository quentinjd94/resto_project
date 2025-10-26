from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, time
from enum import Enum

class OrderType(str, Enum):
    TAKEAWAY = "takeaway"
    DELIVERY = "delivery"

class OrderStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# ===== RESTAURANT =====
class Restaurant(BaseModel):
    id: str
    name: str
    twilio_phone: str
    owner_phone: str
    email: Optional[str] = None
    address: str
    city: str
    custom_prompt: Optional[str] = None
    is_active: bool = True
    assistant_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

# ===== MENU =====
class MenuItemSize(BaseModel):
    senior: Optional[float] = None
    mega: Optional[float] = None
    unique: Optional[float] = None  # Pour items sans taille

class MenuItem(BaseModel):
    id: str
    restaurant_id: str
    name: str
    category: str  # pizza, boisson, dessert, accompagnement
    sizes: MenuItemSize
    description: Optional[str] = None
    available: bool = True

# ===== DELIVERY ZONES =====
class DeliveryZone(BaseModel):
    id: str
    restaurant_id: str
    city: str
    postal_code: str
    streets: List[str]
    min_order_amount: float
    delivery_fee: float = 0.0

# ===== OPENING HOURS =====
class OpeningHour(BaseModel):
    id: str
    restaurant_id: str
    day_of_week: int  # 0=Lundi, 6=Dimanche
    open_time: time
    close_time: time
    is_closed: bool = False

# ===== ORDER =====
class OrderItem(BaseModel):
    name: str
    size: Optional[str] = None
    quantity: int = 1
    unit_price: float
    modifications: Optional[List[str]] = None

class DeliveryAddress(BaseModel):
    street: str
    number: str
    city: str
    postal_code: str
    additional_info: Optional[str] = None  # Étage, digicode, etc.

class Order(BaseModel):
    id: str
    restaurant_id: str
    call_sid: str
    customer_phone: str
    customer_name: Optional[str] = None
    order_type: OrderType
    items: List[OrderItem]
    total_amount: float
    delivery_address: Optional[DeliveryAddress] = None
    status: OrderStatus = OrderStatus.IN_PROGRESS
    created_at: datetime = Field(default_factory=datetime.now)
    conversation_transcript: Optional[List[Dict]] = None

# ===== SMS LOG =====
class SMSLog(BaseModel):
    id: str
    order_id: str
    recipient: str
    message: str
    status: str  # sent, failed, pending
    sent_at: datetime = Field(default_factory=datetime.now)
