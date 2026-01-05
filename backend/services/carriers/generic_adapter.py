"""
Generic Carrier Adapter
Allows admins to add custom carrier integrations without coding

Supports:
- Custom base URLs
- Configurable auth headers
- Dynamic endpoint mapping
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


@dataclass
class GenericCarrierConfig:
    """Configuration for a generic carrier API"""
    id: str
    name: str
    base_url: str
    auth_type: str  # 'bearer', 'api_key', 'basic', 'custom_header'
    auth_header_name: str  # e.g., 'Authorization', 'X-API-Key'
    auth_header_template: str  # e.g., 'Bearer {KEY}', '{KEY}'
    api_key: str = ""
    secret_key: str = ""
    
    # Endpoint mappings (optional)
    create_shipment_endpoint: str = "/shipments"
    track_shipment_endpoint: str = "/tracking/{tracking_id}"
    cancel_shipment_endpoint: str = "/shipments/{tracking_id}/cancel"
    
    # Response field mappings
    tracking_id_field: str = "tracking_id"
    status_field: str = "status"
    
    # Metadata
    logo_color: str = "#1E3A8A"  # Default blue
    is_active: bool = True
    created_at: str = ""
    created_by: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GenericCarrierAdapter:
    """
    Generic adapter that can work with any carrier API
    based on dynamic configuration
    """
    
    def __init__(self, config: GenericCarrierConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _build_auth_header(self) -> Dict[str, str]:
        """Build authentication header based on config"""
        if not self.config.api_key:
            return {}
        
        # Replace {KEY} and {SECRET} placeholders
        value = self.config.auth_header_template
        value = value.replace("{KEY}", self.config.api_key)
        value = value.replace("{SECRET}", self.config.secret_key or "")
        
        return {self.config.auth_header_name: value}
    
    def _build_url(self, endpoint: str, **kwargs) -> str:
        """Build full URL with path parameters"""
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Replace path parameters
        for key, value in kwargs.items():
            url = url.replace(f"{{{key}}}", str(value))
        
        return url
    
    async def create_shipment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shipment with the generic carrier"""
        try:
            url = self._build_url(self.config.create_shipment_endpoint)
            headers = self._build_auth_header()
            headers["Content-Type"] = "application/json"
            
            response = await self.client.post(url, json=order_data, headers=headers)
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "success": True,
                    "tracking_id": data.get(self.config.tracking_id_field, f"GEN-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                    "carrier_response": data
                }
            else:
                return {
                    "success": False,
                    "error": f"API Error {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Generic carrier error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def track_shipment(self, tracking_id: str) -> Dict[str, Any]:
        """Track a shipment"""
        try:
            url = self._build_url(self.config.track_shipment_endpoint, tracking_id=tracking_id)
            headers = self._build_auth_header()
            
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get(self.config.status_field, "unknown"),
                    "carrier_response": data
                }
            else:
                return {
                    "success": False,
                    "error": f"API Error {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Generic carrier tracking error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def close(self):
        await self.client.aclose()


# Pre-configured carriers (including Anderson)
PRECONFIGURED_CARRIERS = {
    "anderson": GenericCarrierConfig(
        id="anderson",
        name="Anderson Logistics",
        base_url="https://api.anderson-logistics.dz/v1",
        auth_type="bearer",
        auth_header_name="Authorization",
        auth_header_template="Bearer {KEY}",
        logo_color="#1E3A8A",  # Navy blue
        create_shipment_endpoint="/parcels/create",
        track_shipment_endpoint="/parcels/{tracking_id}/track",
        tracking_id_field="parcel_id",
        status_field="current_status"
    ),
    "speedz": GenericCarrierConfig(
        id="speedz",
        name="SpeedZ Express",
        base_url="https://api.speedz.dz/api",
        auth_type="api_key",
        auth_header_name="X-API-Key",
        auth_header_template="{KEY}",
        logo_color="#10B981",  # Green
        create_shipment_endpoint="/shipments",
        track_shipment_endpoint="/track/{tracking_id}",
        tracking_id_field="shipment_id",
        status_field="status"
    )
}


def get_preconfigured_carrier(carrier_id: str) -> Optional[GenericCarrierConfig]:
    """Get a pre-configured carrier by ID"""
    return PRECONFIGURED_CARRIERS.get(carrier_id)
