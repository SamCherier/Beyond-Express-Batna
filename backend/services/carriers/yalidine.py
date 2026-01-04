"""
Yalidine API Integration - YalidineAdapter
Official Yalidine v1 API implementation for Algeria delivery

API Documentation: https://api.yalidine.app/
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
import re

from .base import BaseCarrier, ShipmentResponse, TrackingUpdate, ShipmentStatus
from .algeria_wilayas import get_wilaya_id, get_wilaya_name, is_valid_wilaya

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
    Yalidine API v1 Adapter
    
    Handles authentication and data mapping for Yalidine delivery API.
    
    Required credentials:
      - api_key: API ID from Yalidine dashboard
      - api_token: API Token from Yalidine dashboard
      - center_id: Your center/depot ID (optional, for stop desk)
    """
    
    # API URLs
    PRODUCTION_URL = "https://api.yalidine.app/v1"
    SANDBOX_URL = "https://api.yalidine.app/v1"  # Yalidine may use same URL with test flag
    
    def __init__(self, credentials: Dict[str, str], test_mode: bool = True):
        super().__init__(credentials, test_mode)
        self.carrier_name = "Yalidine"
        
        # API endpoint - Yalidine uses same endpoint for test/prod
        # Authentication headers determine sandbox vs production
        self.base_url = self.SANDBOX_URL if test_mode else self.PRODUCTION_URL
        
        # Extract credentials
        self.api_key = credentials.get('api_key', '').strip()
        self.api_token = credentials.get('api_token', '').strip() or credentials.get('center_id', '').strip()
        self.center_id = credentials.get('center_id', '').strip()
        
        logger.info(f"🚚 YalidineAdapter initialized (test_mode={test_mode}, api_key={self.api_key[:8]}...)")
    
    def _get_headers(self) -> Dict[str, str]:
        """Build authentication headers for Yalidine API"""
        return {
            "X-API-ID": self.api_key,
            "X-API-TOKEN": self.api_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _parse_customer_name(self, full_name: str) -> tuple:
        """
        Split customer full name into firstname and lastname
        
        Args:
            full_name: Full customer name (e.g., "Ahmed Benali")
            
        Returns:
            Tuple of (firstname, lastname)
        """
        if not full_name:
            return ("Client", "")
        
        parts = full_name.strip().split()
        
        if len(parts) == 1:
            return (parts[0], "")
        elif len(parts) == 2:
            return (parts[0], parts[1])
        else:
            # First name is first word, last name is everything else
            return (parts[0], " ".join(parts[1:]))
    
    def _format_phone(self, phone: str) -> str:
        """
        Format phone number for Yalidine API
        
        Yalidine expects: 05XXXXXXXX or 06XXXXXXXX or 07XXXXXXXX (10 digits)
        """
        if not phone:
            return ""
        
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Handle international format (+213)
        if digits.startswith('213'):
            digits = '0' + digits[3:]
        
        # Ensure starts with 0
        if len(digits) == 9 and digits[0] in ['5', '6', '7']:
            digits = '0' + digits
        
        # Validate length
        if len(digits) != 10:
            logger.warning(f"⚠️ Phone number format issue: {phone} -> {digits}")
        
        return digits
    
    def _map_order_to_parcel(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Beyond Express order fields to Yalidine parcel format
        
        Beyond Express Order:
            - tracking_id
            - recipient: {name, phone, address, wilaya, commune}
            - sender: {name, phone, address, wilaya}
            - cod_amount (prix)
            - description (product list)
            - free_shipping
            - weight
            - delivery_type
            
        Yalidine Parcel:
            - order_id
            - firstname, familyname
            - contact_phone
            - address
            - to_wilaya_name (or to_wilaya_id)
            - to_commune_name (or to_commune_id)
            - from_wilaya_name
            - product_list
            - price (COD)
            - freeshipping
            - weight
            - is_stopdesk
        """
        recipient = order_data.get('recipient', {})
        sender = order_data.get('sender', {})
        
        # Parse customer name
        firstname, familyname = self._parse_customer_name(recipient.get('name', ''))
        
        # Format phone
        phone = self._format_phone(recipient.get('phone', ''))
        
        # Get wilaya IDs
        dest_wilaya = recipient.get('wilaya', 'Alger')
        origin_wilaya = sender.get('wilaya', 'Batna')
        
        # Build parcel data
        parcel = {
            # Reference
            "order_id": order_data.get('tracking_id', ''),
            
            # Customer info
            "firstname": firstname,
            "familyname": familyname,
            "contact_phone": phone,
            
            # Address - use wilaya names (Yalidine accepts both names and IDs)
            "address": recipient.get('address', ''),
            "to_wilaya_name": dest_wilaya,
            "to_commune_name": recipient.get('commune', ''),
            "from_wilaya_name": origin_wilaya,
            
            # Product info
            "product_list": order_data.get('description', '') or order_data.get('product_name', 'Colis e-commerce'),
            
            # COD (Cash on Delivery)
            "price": int(order_data.get('cod_amount', 0)),
            "declared_value": int(order_data.get('cod_amount', 0)),
            
            # Shipping options
            "freeshipping": order_data.get('free_shipping', False),
            "do_insurance": False,
            "has_exchange": False,
            "product_to_collect": "",
            
            # Package dimensions (defaults)
            "weight": float(order_data.get('weight', 1)),
            "height": 10,
            "width": 20,
            "length": 30,
            
            # Delivery type
            "is_stopdesk": order_data.get('delivery_type', '').lower() in ['stopdesk', 'bureau', 'point relais'],
        }
        
        # Add stop desk ID if applicable
        if parcel['is_stopdesk'] and self.center_id:
            try:
                parcel['stopdesk_id'] = int(self.center_id)
            except ValueError:
                pass
        
        return parcel
    
    async def validate_credentials(self) -> bool:
        """
        Test if API credentials are valid by fetching wilayas list
        
        Returns:
            True if credentials are valid and API is accessible
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/wilayas",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Yalidine returns list of wilayas if authenticated
                    if isinstance(data, list) or (isinstance(data, dict) and 'data' in data):
                        logger.info("✅ Yalidine credentials validated successfully")
                        return True
                
                logger.error(f"❌ Yalidine auth failed: {response.status_code} - {response.text[:200]}")
                return False
                    
        except httpx.TimeoutException:
            logger.error("❌ Yalidine validation timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Yalidine validation error: {str(e)}")
            return False
    
    async def create_shipment(self, order_data: Dict[str, Any]) -> ShipmentResponse:
        """
        Create a parcel with Yalidine API
        
        Args:
            order_data: Order data from Beyond Express database
            
        Returns:
            ShipmentResponse with tracking ID and status
        """
        try:
            # Map order to Yalidine format
            parcel = self._map_order_to_parcel(order_data)
            
            logger.info(f"📦 Creating Yalidine parcel: {parcel['order_id']}")
            logger.debug(f"Parcel data: {parcel}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Yalidine API expects array of parcels
                response = await client.post(
                    f"{self.base_url}/parcels",
                    headers=self._get_headers(),
                    json=[parcel]
                )
                
                logger.info(f"Yalidine response: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    
                    # Parse response - Yalidine returns array or object with data key
                    if isinstance(data, list) and len(data) > 0:
                        result = data[0]
                    elif isinstance(data, dict):
                        if 'data' in data and isinstance(data['data'], list):
                            result = data['data'][0] if data['data'] else {}
                        else:
                            result = data
                    else:
                        result = {}
                    
                    # Extract tracking ID
                    tracking_id = (
                        result.get('tracking') or 
                        result.get('tracking_id') or 
                        result.get('code') or
                        ''
                    )
                    
                    if tracking_id:
                        logger.info(f"✅ Yalidine parcel created successfully: {tracking_id}")
                        
                        return ShipmentResponse(
                            success=True,
                            carrier_tracking_id=tracking_id,
                            carrier_name=self.carrier_name,
                            label_url=result.get('label_url') or result.get('label'),
                            shipping_cost=result.get('delivery_fee') or result.get('fee'),
                            raw_response=result
                        )
                    else:
                        # Success but no tracking ID in response
                        logger.warning(f"⚠️ Yalidine: No tracking ID in response: {data}")
                        return ShipmentResponse(
                            success=False,
                            carrier_name=self.carrier_name,
                            error_message="Aucun code de suivi reçu de Yalidine",
                            raw_response=data
                        )
                
                # Handle error responses
                try:
                    error_data = response.json()
                except:
                    error_data = {"message": response.text[:500]}
                
                error_msg = (
                    error_data.get('message') or 
                    error_data.get('error') or 
                    error_data.get('errors', [{}])[0].get('message') if isinstance(error_data.get('errors'), list) else None or
                    f"Erreur API Yalidine ({response.status_code})"
                )
                
                logger.error(f"❌ Yalidine error: {error_msg}")
                
                return ShipmentResponse(
                    success=False,
                    carrier_name=self.carrier_name,
                    error_message=str(error_msg),
                    raw_response=error_data
                )
                    
        except httpx.TimeoutException:
            logger.error("❌ Yalidine create_shipment timeout")
            return ShipmentResponse(
                success=False,
                carrier_name=self.carrier_name,
                error_message="Timeout - L'API Yalidine n'a pas répondu"
            )
        except Exception as e:
            logger.error(f"❌ Yalidine create_shipment error: {str(e)}")
            return ShipmentResponse(
                success=False,
                carrier_name=self.carrier_name,
                error_message=f"Erreur: {str(e)}"
            )
    
    async def get_tracking(self, tracking_id: str) -> List[TrackingUpdate]:
        """
        Get tracking history for a Yalidine parcel
        
        Args:
            tracking_id: Yalidine tracking code
            
        Returns:
            List of tracking updates
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
                    
                    # Handle different response formats
                    if isinstance(data, dict) and 'data' in data:
                        parcels = data['data'] if isinstance(data['data'], list) else [data['data']]
                    elif isinstance(data, list):
                        parcels = data
                    else:
                        parcels = [data]
                    
                    if not parcels:
                        return []
                    
                    parcel = parcels[0]
                    updates = []
                    
                    # Get status history if available
                    histories = parcel.get('histories', []) or parcel.get('history', []) or []
                    
                    for h in histories:
                        status_text = h.get('status', '') or h.get('state', '')
                        updates.append(TrackingUpdate(
                            status=self.map_status_to_internal(status_text),
                            timestamp=h.get('created_at') or h.get('date') or datetime.now().isoformat(),
                            location=h.get('center') or h.get('location', ''),
                            description=status_text,
                            carrier_status_code=status_text
                        ))
                    
                    # If no history, add current status
                    if not updates:
                        current_status = parcel.get('status') or parcel.get('state', 'En préparation')
                        updates.append(TrackingUpdate(
                            status=self.map_status_to_internal(current_status),
                            timestamp=parcel.get('updated_at') or datetime.now().isoformat(),
                            description=current_status
                        ))
                    
                    return updates
                    
        except Exception as e:
            logger.error(f"❌ Yalidine get_tracking error: {str(e)}")
        
        return []
    
    async def cancel_shipment(self, tracking_id: str) -> bool:
        """
        Cancel a Yalidine parcel (if still possible)
        
        Note: Not all parcels can be cancelled depending on their status
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.delete(
                    f"{self.base_url}/parcels/{tracking_id}",
                    headers=self._get_headers()
                )
                
                if response.status_code in [200, 204]:
                    logger.info(f"✅ Yalidine parcel cancelled: {tracking_id}")
                    return True
                    
                logger.warning(f"⚠️ Yalidine cancel failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Yalidine cancel error: {str(e)}")
            return False
    
    async def get_label(self, tracking_id: str) -> Optional[bytes]:
        """
        Download shipping label PDF from Yalidine
        
        Args:
            tracking_id: Yalidine tracking code
            
        Returns:
            PDF bytes or None
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try direct label endpoint first
                label_response = await client.get(
                    f"{self.base_url}/parcels/{tracking_id}/label",
                    headers=self._get_headers()
                )
                
                if label_response.status_code == 200:
                    content_type = label_response.headers.get('content-type', '')
                    if 'pdf' in content_type or 'octet' in content_type:
                        return label_response.content
                
                # Try getting parcel info to find label URL
                response = await client.get(
                    f"{self.base_url}/parcels",
                    headers=self._get_headers(),
                    params={"tracking": tracking_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    parcels = data if isinstance(data, list) else data.get('data', [data])
                    
                    if parcels:
                        label_url = parcels[0].get('label_url') or parcels[0].get('label')
                        
                        if label_url:
                            label_response = await client.get(label_url)
                            if label_response.status_code == 200:
                                return label_response.content
                    
        except Exception as e:
            logger.error(f"❌ Yalidine get_label error: {str(e)}")
        
        return None
    
    async def get_rates(self, origin_wilaya: str, dest_wilaya: str, weight: float = 1.0) -> Optional[float]:
        """
        Get shipping rate from Yalidine API
        
        Args:
            origin_wilaya: Origin wilaya name
            dest_wilaya: Destination wilaya name
            weight: Package weight in kg
            
        Returns:
            Shipping cost in DZD or None
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/fees",
                    headers=self._get_headers(),
                    params={
                        "from_wilaya_name": origin_wilaya,
                        "to_wilaya_name": dest_wilaya,
                        "weight": weight
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return (
                        data.get('home_fee') or 
                        data.get('fee') or 
                        data.get('price') or
                        data.get('delivery_fee')
                    )
                    
        except Exception as e:
            logger.error(f"❌ Yalidine get_rates error: {str(e)}")
        
        return None
    
    async def get_wilayas(self) -> List[Dict[str, Any]]:
        """Get list of wilayas supported by Yalidine"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/wilayas",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data if isinstance(data, list) else data.get('data', [])
                    
        except Exception as e:
            logger.error(f"❌ Yalidine get_wilayas error: {str(e)}")
        
        return []
    
    async def get_communes(self, wilaya_id: int) -> List[Dict[str, Any]]:
        """Get communes for a specific wilaya"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/communes/{wilaya_id}",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data if isinstance(data, list) else data.get('data', [])
                    
        except Exception as e:
            logger.error(f"❌ Yalidine get_communes error: {str(e)}")
        
        return []
    
    def map_status_to_internal(self, carrier_status: str) -> ShipmentStatus:
        """Map Yalidine status to internal status"""
        return YALIDINE_STATUS_MAP.get(carrier_status, ShipmentStatus.IN_TRANSIT)


# Alias for backward compatibility
YalidineAdapter = YalidineCarrier
