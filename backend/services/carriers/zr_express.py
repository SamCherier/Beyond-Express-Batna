"""
ZR Express Mock Adapter
Simulated carrier for testing Smart Router functionality

This is a MOCK implementation that simulates ZR Express API responses
for development and testing purposes.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import random

from .base import BaseCarrier, ShipmentResponse, TrackingUpdate, ShipmentStatus

logger = logging.getLogger(__name__)


class ZRExpressCarrier(BaseCarrier):
    """
    ZR Express Mock Adapter
    
    Simulates ZR Express API for testing the Smart Router.
    ZR Express is known for coverage in remote/southern Algeria wilayas.
    
    MOCK MODE: All operations are simulated
    """
    
    # Wilayas where ZR Express has better coverage (southern Algeria)
    ZR_COVERAGE_WILAYAS = [
        "Adrar", "Tamanrasset", "Béchar", "Bechar", "Tindouf", "Illizi",
        "El Oued", "Ouargla", "Ghardaïa", "Ghardaia", "Laghouat",
        "Biskra", "El Bayadh", "Naâma", "Naama"
    ]
    
    def __init__(self, credentials: Dict[str, str], test_mode: bool = True):
        super().__init__(credentials, test_mode)
        self.carrier_name = "ZR Express"
        self.base_url = "https://api.zr-express.com/v1"  # Placeholder
        self.is_mock = True
        
        logger.info(f"🚛 ZRExpressCarrier initialized (MOCK MODE)")
    
    def _get_headers(self) -> Dict[str, str]:
        """Build authentication headers"""
        return {
            "Authorization": f"Bearer {self.credentials.get('api_key', '')}",
            "Content-Type": "application/json"
        }
    
    async def validate_credentials(self) -> bool:
        """
        Mock credential validation - always returns True in mock mode
        """
        logger.info("✅ ZR Express credentials validated (MOCK)")
        return True
    
    async def create_shipment(self, order_data: Dict[str, Any]) -> ShipmentResponse:
        """
        Mock shipment creation
        
        Simulates successful shipment creation and returns a mock tracking ID
        """
        try:
            recipient = order_data.get('recipient', {})
            tracking_id = order_data.get('tracking_id', '')
            
            # Generate mock ZR tracking ID
            mock_tracking = f"ZR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Simulate some delay and random success/failure
            # In production, this would call the real ZR Express API
            
            logger.info(f"📦 [MOCK] ZR Express shipment created: {mock_tracking}")
            logger.info(f"   Destination: {recipient.get('wilaya', 'N/A')} - {recipient.get('commune', 'N/A')}")
            
            # Simulate random processing fee (southern Algeria is more expensive)
            base_fee = 800  # DZD
            wilaya = recipient.get('wilaya', '')
            if wilaya in self.ZR_COVERAGE_WILAYAS:
                shipping_cost = base_fee + random.randint(200, 500)
            else:
                shipping_cost = base_fee + random.randint(100, 300)
            
            return ShipmentResponse(
                success=True,
                carrier_tracking_id=mock_tracking,
                carrier_name=self.carrier_name,
                label_url=f"https://api.zr-express.com/labels/{mock_tracking}.pdf",
                shipping_cost=shipping_cost,
                estimated_delivery=f"{random.randint(2, 5)} jours",
                raw_response={
                    "mock": True,
                    "tracking": mock_tracking,
                    "status": "created",
                    "message": "Colis créé avec succès (Simulation)"
                }
            )
            
        except Exception as e:
            logger.error(f"❌ ZR Express mock error: {str(e)}")
            return ShipmentResponse(
                success=False,
                carrier_name=self.carrier_name,
                error_message=f"Erreur simulation: {str(e)}"
            )
    
    async def get_tracking(self, tracking_id: str) -> List[TrackingUpdate]:
        """
        Mock tracking history
        """
        # Return simulated tracking history
        now = datetime.now()
        
        return [
            TrackingUpdate(
                status=ShipmentStatus.CREATED,
                timestamp=(now.replace(hour=8)).isoformat(),
                location="Centre de tri ZR - Alger",
                description="Colis enregistré",
                carrier_status_code="REGISTERED"
            ),
            TrackingUpdate(
                status=ShipmentStatus.IN_TRANSIT,
                timestamp=(now.replace(hour=14)).isoformat(),
                location="Hub Sud - Ghardaïa",
                description="En transit vers destination",
                carrier_status_code="IN_TRANSIT"
            )
        ]
    
    async def cancel_shipment(self, tracking_id: str) -> bool:
        """Mock cancellation"""
        logger.info(f"📦 [MOCK] ZR Express shipment cancelled: {tracking_id}")
        return True
    
    async def get_label(self, tracking_id: str) -> Optional[bytes]:
        """Mock label download - returns None in mock mode"""
        logger.warning(f"⚠️ ZR Express label download not available in mock mode")
        return None
    
    async def get_rates(self, origin_wilaya: str, dest_wilaya: str, weight: float = 1.0) -> Optional[float]:
        """
        Mock rate calculation
        
        ZR Express is generally more expensive but has better coverage
        for southern/remote wilayas
        """
        base_rate = 600  # DZD
        
        # Southern wilayas have higher rates
        southern_wilayas = ["Adrar", "Tamanrasset", "Tindouf", "Illizi", "Djanet"]
        
        if dest_wilaya in southern_wilayas:
            return base_rate + 400 + (weight * 50)
        else:
            return base_rate + 200 + (weight * 30)
    
    def map_status_to_internal(self, carrier_status: str) -> ShipmentStatus:
        """Map ZR Express status to internal status"""
        status_map = {
            "REGISTERED": ShipmentStatus.CREATED,
            "PICKED_UP": ShipmentStatus.PICKED_UP,
            "IN_TRANSIT": ShipmentStatus.IN_TRANSIT,
            "OUT_FOR_DELIVERY": ShipmentStatus.OUT_FOR_DELIVERY,
            "DELIVERED": ShipmentStatus.DELIVERED,
            "FAILED": ShipmentStatus.FAILED,
            "RETURNED": ShipmentStatus.RETURNED,
        }
        return status_map.get(carrier_status, ShipmentStatus.IN_TRANSIT)
    
    @classmethod
    def has_coverage(cls, wilaya: str) -> bool:
        """
        Check if ZR Express has good coverage for a wilaya
        
        ZR Express specializes in southern/remote Algeria
        """
        normalized = wilaya.strip().lower()
        for w in cls.ZR_COVERAGE_WILAYAS:
            if w.lower() == normalized or normalized in w.lower():
                return True
        return False


# Alias
ZRExpressAdapter = ZRExpressCarrier
