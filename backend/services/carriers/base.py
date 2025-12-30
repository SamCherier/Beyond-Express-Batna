"""
Base Carrier Interface
All carrier integrations must implement this interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ShipmentStatus(str, Enum):
    """Standardized shipment statuses across all carriers"""
    CREATED = "created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"
    CANCELLED = "cancelled"


@dataclass
class ShipmentResponse:
    """Standardized response from carrier API"""
    success: bool
    carrier_tracking_id: Optional[str] = None
    carrier_name: str = ""
    label_url: Optional[str] = None
    label_pdf: Optional[bytes] = None
    estimated_delivery: Optional[str] = None
    shipping_cost: Optional[float] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class TrackingUpdate:
    """Standardized tracking update"""
    status: ShipmentStatus
    timestamp: str
    location: Optional[str] = None
    description: Optional[str] = None
    carrier_status_code: Optional[str] = None


class BaseCarrier(ABC):
    """
    Abstract base class for all carrier integrations
    Each carrier (Yalidine, DHD, ZR Express, etc.) must implement these methods
    """
    
    def __init__(self, credentials: Dict[str, str], test_mode: bool = True):
        self.credentials = credentials
        self.test_mode = test_mode
        self.carrier_name = "Unknown"
        self.base_url = ""
    
    @abstractmethod
    async def create_shipment(self, order_data: Dict[str, Any]) -> ShipmentResponse:
        """
        Create a new shipment/parcel with the carrier
        
        Args:
            order_data: Order information from our database
            
        Returns:
            ShipmentResponse with tracking ID and label
        """
        pass
    
    @abstractmethod
    async def get_tracking(self, tracking_id: str) -> List[TrackingUpdate]:
        """
        Get tracking history for a shipment
        
        Args:
            tracking_id: Carrier's tracking ID
            
        Returns:
            List of tracking updates
        """
        pass
    
    @abstractmethod
    async def cancel_shipment(self, tracking_id: str) -> bool:
        """
        Cancel a shipment if possible
        
        Args:
            tracking_id: Carrier's tracking ID
            
        Returns:
            True if cancelled successfully
        """
        pass
    
    @abstractmethod
    async def get_label(self, tracking_id: str) -> Optional[bytes]:
        """
        Download shipping label PDF
        
        Args:
            tracking_id: Carrier's tracking ID
            
        Returns:
            PDF bytes or None
        """
        pass
    
    @abstractmethod
    async def get_rates(self, origin_wilaya: str, dest_wilaya: str, weight: float = 1.0) -> Optional[float]:
        """
        Get shipping rate for a route
        
        Args:
            origin_wilaya: Origin wilaya name
            dest_wilaya: Destination wilaya name
            weight: Package weight in kg
            
        Returns:
            Shipping cost in DZD or None if not available
        """
        pass
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """
        Test if the API credentials are valid
        
        Returns:
            True if credentials are valid
        """
        pass
    
    def map_status_to_internal(self, carrier_status: str) -> ShipmentStatus:
        """
        Map carrier-specific status to our internal status
        Override in subclass for carrier-specific mapping
        """
        return ShipmentStatus.IN_TRANSIT
