"""
Yalidine API Integration
Official Yalidine v1 API implementation for Algeria delivery

API Documentation: https://www.yalidine.com/
Endpoints:
  - POST /v1/parcels - Create parcels
  - GET /v1/parcels - Retrieve parcels by tracking
  - GET /v1/wilayas - Get wilayas list
  - GET /v1/communes - Get communes for a wilaya
  - GET /v1/centers - Get stop desk centers
  - GET /v1/fees - Get delivery fees
"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import base64

from .base import BaseCarrier, ShipmentResponse, TrackingUpdate, ShipmentStatus

logger = logging.getLogger(__name__)


# Yalidine status mapping to internal status
YALIDINE_STATUS_MAP = {
    "En préparation": ShipmentStatus.CREATED,
    "Prêt à expédier": ShipmentStatus.CREATED,
    "Expédié vers le centre": ShipmentStatus.IN_TRANSIT,
    "Reçu au centre": ShipmentStatus.IN_TRANSIT,
    "En cours de livraison": ShipmentStatus.OUT_FOR_DELIVERY,
    "En attente du client": ShipmentStatus.OUT_FOR_DELIVERY,
    "Livré": ShipmentStatus.DELIVERED,
    "Echec livraison": ShipmentStatus.FAILED,
    "Retour en cours": ShipmentStatus.RETURNED,
    "Retourné": ShipmentStatus.RETURNED,
    "Annulé": ShipmentStatus.CANCELLED,
}


class YalidineCarrier(BaseCarrier):
    """
    Yalidine API v1 Integration
    
    Required credentials:
      - api_key: API ID from Yalidine dashboard
      - api_token: API Token from Yalidine dashboard
      - center_id: Your center/depot ID (optional, for stop desk)
    """
    
    def __init__(self, credentials: Dict[str, str], test_mode: bool = True):
        super().__init__(credentials, test_mode)
        self.carrier_name = "Yalidine"
        
        # API endpoints
        if test_mode:
            self.base_url = "https://sandbox.yalidine.app/v1"
        else:
            self.base_url = "https://api.yalidine.app/v1"
        
        # Extract credentials
        self.api_key = credentials.get('api_key', '')
        self.api_token = credentials.get('api_token') or credentials.get('center_id', '')
        self.center_id = credentials.get('center_id', '')
        
        logger.info(f"🚚 YalidineCarrier initialized (test_mode={test_mode})")
    
    def _get_headers(self) -> Dict[str, str]:
        """Build authentication headers"""
        return {
            "X-API-ID": self.api_key,
            "X-API-TOKEN": self.api_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def validate_credentials(self) -> bool:
        """
        Test if credentials are valid by fetching wilayas list
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/wilayas",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    logger.info("✅ Yalidine credentials validated")
                    return True
                else:
                    logger.error(f"❌ Yalidine auth failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Yalidine validation error: {str(e)}")
            return False
    
    async def create_shipment(self, order_data: Dict[str, Any]) -> ShipmentResponse:
        """
        Create a parcel with Yalidine API
        
        Maps Beyond Express order fields to Yalidine API format
        """
        try:
            recipient = order_data.get('recipient', {})
            sender = order_data.get('sender', {})
            
            # Build parcel data according to Yalidine API spec
            parcel = {
                "order_id": order_data.get('tracking_id', ''),
                "from_wilaya_name": sender.get('wilaya', 'Batna'),
                "firstname": recipient.get('name', '').split()[0] if recipient.get('name') else '',
                "familyname": ' '.join(recipient.get('name', '').split()[1:]) if len(recipient.get('name', '').split()) > 1 else recipient.get('name', ''),
                "contact_phone": recipient.get('phone', ''),
                "address": recipient.get('address', ''),
                "to_commune_name": recipient.get('commune', ''),
                "to_wilaya_name": recipient.get('wilaya', ''),
                "product_list": order_data.get('description', 'Colis e-commerce'),
                "price": order_data.get('cod_amount', 0),
                "do_insurance": False,
                "declared_value": order_data.get('cod_amount', 0),
                "height": 10,
                "width": 20,
                "length": 30,
                "weight": order_data.get('weight', 1),
                "freeshipping": order_data.get('free_shipping', False),
                "is_stopdesk": order_data.get('delivery_type', '') == 'Livraison au Bureau',
                "has_exchange": False,
                "product_to_collect": ""
            }
            
            # Add stop desk ID if applicable
            if parcel['is_stopdesk'] and self.center_id:
                parcel['stopdesk_id'] = int(self.center_id)
            
            logger.info(f"📦 Creating Yalidine parcel: {parcel['order_id']}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/parcels",
                    headers=self._get_headers(),
                    json=[parcel]  # API expects array
                )
                
                logger.info(f"Yalidine response: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    
                    # Parse response - Yalidine returns array
                    if isinstance(data, list) and len(data) > 0:
                        result = data[0]
                    elif isinstance(data, dict):
                        result = data
                    else:
                        result = {}
                    
                    tracking_id = result.get('tracking', '') or result.get('tracking_id', '')
                    
                    logger.info(f"✅ Yalidine parcel created: {tracking_id}")
                    
                    return ShipmentResponse(
                        success=True,
                        carrier_tracking_id=tracking_id,
                        carrier_name=self.carrier_name,
                        label_url=result.get('label_url'),
                        shipping_cost=result.get('delivery_fee'),
                        raw_response=result
                    )
                else:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('message', f'API Error {response.status_code}')
                    
                    logger.error(f"❌ Yalidine error: {error_msg}")
                    
                    return ShipmentResponse(
                        success=False,
                        carrier_name=self.carrier_name,
                        error_message=error_msg,
                        raw_response=error_data
                    )
                    
        except Exception as e:
            logger.error(f"❌ Yalidine create_shipment error: {str(e)}")
            return ShipmentResponse(
                success=False,
                carrier_name=self.carrier_name,
                error_message=str(e)
            )
    
    async def get_tracking(self, tracking_id: str) -> List[TrackingUpdate]:
        """
        Get tracking history for a Yalidine parcel
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/parcels",
                    headers=self._get_headers(),
                    params={"tracking": tracking_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    parcels = data if isinstance(data, list) else [data]
                    
                    if not parcels:
                        return []
                    
                    parcel = parcels[0]
                    updates = []
                    
                    # Get status history if available
                    histories = parcel.get('histories', []) or []
                    
                    for h in histories:
                        status_text = h.get('status', '')
                        updates.append(TrackingUpdate(
                            status=self.map_status_to_internal(status_text),
                            timestamp=h.get('created_at', datetime.now().isoformat()),
                            location=h.get('center', ''),
                            description=status_text,
                            carrier_status_code=status_text
                        ))
                    
                    # If no history, add current status
                    if not updates:
                        updates.append(TrackingUpdate(
                            status=self.map_status_to_internal(parcel.get('status', '')),
                            timestamp=parcel.get('updated_at', datetime.now().isoformat()),
                            description=parcel.get('status', 'En préparation')
                        ))
                    
                    return updates
                    
        except Exception as e:
            logger.error(f"❌ Yalidine get_tracking error: {str(e)}")
            return []
        
        return []
    
    async def cancel_shipment(self, tracking_id: str) -> bool:
        """
        Cancel a Yalidine parcel (if still possible)
        """
        try:
            # Yalidine may not have a direct cancel endpoint
            # This would need to be verified with actual API docs
            logger.warning(f"⚠️ Yalidine cancel not implemented for {tracking_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Yalidine cancel error: {str(e)}")
            return False
    
    async def get_label(self, tracking_id: str) -> Optional[bytes]:
        """
        Download shipping label PDF from Yalidine
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First get parcel info to find label URL
                response = await client.get(
                    f"{self.base_url}/parcels",
                    headers=self._get_headers(),
                    params={"tracking": tracking_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    parcels = data if isinstance(data, list) else [data]
                    
                    if parcels and parcels[0].get('label_url'):
                        label_url = parcels[0]['label_url']
                        
                        # Download label PDF
                        label_response = await client.get(label_url)
                        if label_response.status_code == 200:
                            return label_response.content
                
                # Try direct label endpoint
                label_response = await client.get(
                    f"{self.base_url}/labels/{tracking_id}",
                    headers=self._get_headers()
                )
                
                if label_response.status_code == 200:
                    return label_response.content
                    
        except Exception as e:
            logger.error(f"❌ Yalidine get_label error: {str(e)}")
        
        return None
    
    async def get_rates(self, origin_wilaya: str, dest_wilaya: str, weight: float = 1.0) -> Optional[float]:
        """
        Get shipping rate from Yalidine API
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/fees",
                    headers=self._get_headers(),
                    params={
                        "from_wilaya": origin_wilaya,
                        "to_wilaya": dest_wilaya,
                        "weight": weight
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('fee') or data.get('price') or data.get('home_fee')
                    
        except Exception as e:
            logger.error(f"❌ Yalidine get_rates error: {str(e)}")
        
        return None
    
    async def get_wilayas(self) -> List[Dict[str, Any]]:
        """
        Get list of wilayas supported by Yalidine
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/wilayas",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"❌ Yalidine get_wilayas error: {str(e)}")
        
        return []
    
    async def get_communes(self, wilaya_id: int) -> List[Dict[str, Any]]:
        """
        Get communes for a specific wilaya
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/communes/{wilaya_id}",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"❌ Yalidine get_communes error: {str(e)}")
        
        return []
    
    def map_status_to_internal(self, carrier_status: str) -> ShipmentStatus:
        """
        Map Yalidine status to internal status
        """
        return YALIDINE_STATUS_MAP.get(carrier_status, ShipmentStatus.IN_TRANSIT)
