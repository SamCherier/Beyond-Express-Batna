"""
Smart Routing Engine v2
Intelligent carrier selection and order synchronization

Features:
  - AI-powered carrier recommendation based on geography
  - Automatic carrier selection based on coverage, cost, speed
  - Order synchronization with carrier APIs
  - Multi-carrier support with fallback handling
  - Real-time routing decisions
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os

from .carriers.base import BaseCarrier, ShipmentResponse, ShipmentStatus
from .carriers.yalidine import YalidineCarrier
from .carriers.zr_express import ZRExpressCarrier

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Strategy for selecting carrier"""
    SMART = "smart"        # AI-powered automatic selection (DEFAULT)
    CHEAPEST = "cheapest"  # Select lowest cost carrier
    FASTEST = "fastest"    # Select fastest delivery carrier
    PRIORITY = "priority"  # Use configured priority order
    COVERAGE = "coverage"  # Best coverage for destination
    BALANCED = "balanced"  # Balance cost and speed


@dataclass
class CarrierRecommendation:
    """Recommendation result from Smart Router"""
    carrier_type: str
    carrier_name: str
    confidence: float  # 0.0 to 1.0
    reason: str
    estimated_cost: Optional[float] = None
    estimated_days: Optional[int] = None
    is_fallback: bool = False
    rules_applied: List[str] = field(default_factory=list)


@dataclass
class CarrierScore:
    """Score for ranking carriers"""
    carrier_type: str
    carrier_name: str
    score: float
    cost: Optional[float] = None
    estimated_days: Optional[int] = None
    coverage_score: float = 1.0
    reason: str = ""


class SmartRouter:
    """
    Smart Routing Engine v2
    
    AI-powered carrier selection based on:
    - Geographic coverage (primary rule)
    - Cost optimization
    - Delivery speed
    - Carrier availability
    - Historical performance
    """
    
    # Carrier classes registry
    CARRIER_CLASSES = {
        "yalidine": YalidineCarrier,
        "zr_express": ZRExpressCarrier,
        # Add more carriers here:
        # "dhd": DHDCarrier,
        # "maystro": MaystroCarrier,
    }
    
    # Geographic routing rules
    # Wilayas best served by ZR Express (southern/remote Algeria)
    ZR_EXPRESS_WILAYAS = [
        "Adrar", "Tamanrasset", "Béchar", "Bechar", "Tindouf", "Illizi",
        "El Oued", "Ouargla", "Ghardaïa", "Ghardaia", "Laghouat",
        "Biskra", "El Bayadh", "Naâma", "Naama", "Djanet",
        "Timimoun", "Bordj Badji Mokhtar", "In Salah", "In Guezzam",
        "Touggourt", "El M'Ghair", "El Meniaa", "Ouled Djellal"
    ]
    
    # Wilayas best served by Yalidine (northern/coastal Algeria)
    YALIDINE_WILAYAS = [
        "Alger", "Oran", "Constantine", "Annaba", "Sétif", "Setif",
        "Blida", "Batna", "Djelfa", "Tizi Ouzou", "Béjaïa", "Bejaia",
        "Tlemcen", "Skikda", "Chlef", "Mostaganem", "Médéa", "Medea",
        "Boumerdès", "Boumerdes", "Tipaza", "Jijel", "Mila", "Guelma",
        "Souk Ahras", "El Tarf", "Bouira", "M'Sila", "Msila",
        "Bordj Bou Arréridj", "Bordj Bou Arreridj", "Khenchela",
        "Oum El Bouaghi", "Tébessa", "Tebessa", "Tiaret", "Mascara",
        "Saïda", "Saida", "Sidi Bel Abbès", "Sidi Bel Abbes",
        "Aïn Defla", "Ain Defla", "Aïn Témouchent", "Ain Temouchent",
        "Relizane", "Tissemsilt"
    ]
    
    # Default carrier priority
    DEFAULT_PRIORITY = ["yalidine", "zr_express", "dhd", "maystro", "guepex"]
    
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'beyond_express_db')
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.db_name]
        
        logger.info("🧠 SmartRouter v2 initialized with AI routing")
    
    def _normalize_wilaya(self, wilaya: str) -> str:
        """Normalize wilaya name for matching"""
        if not wilaya:
            return ""
        # Remove accents and normalize
        replacements = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'î': 'i', 'ï': 'i',
            'ô': 'o', 'ö': 'o',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', "'": " ", "-": " "
        }
        result = wilaya.lower().strip()
        for old, new in replacements.items():
            result = result.replace(old, new)
        return result
    
    def _check_wilaya_match(self, wilaya: str, wilaya_list: List[str]) -> bool:
        """Check if a wilaya matches any in a list"""
        normalized = self._normalize_wilaya(wilaya)
        for w in wilaya_list:
            if self._normalize_wilaya(w) == normalized:
                return True
        return False
    
    async def recommend_carrier(self, order: Dict[str, Any], user_id: str) -> CarrierRecommendation:
        """
        🧠 AI-Powered Carrier Recommendation
        
        Analyzes the order and returns the best carrier recommendation
        based on geographic rules and carrier availability.
        
        Args:
            order: Order data with recipient info
            user_id: User ID to check carrier configurations
            
        Returns:
            CarrierRecommendation with carrier_type and reasoning
        """
        recipient = order.get('recipient', {})
        dest_wilaya = recipient.get('wilaya', '')
        rules_applied = []
        
        logger.info(f"🧠 Analyzing order for Smart Routing: Wilaya={dest_wilaya}")
        
        # Get user's active carriers
        active_carriers = await self.get_active_carriers(user_id)
        active_types = [c.get('carrier_type') for c in active_carriers]
        
        # ===== RULE 1: Geographic Coverage (Primary) =====
        
        # Check if destination is in ZR Express territory (southern Algeria)
        if self._check_wilaya_match(dest_wilaya, self.ZR_EXPRESS_WILAYAS):
            rules_applied.append("Règle Géographique: Wilaya du Sud")
            
            # Check if ZR Express is available for user
            if 'zr_express' in active_types:
                logger.info(f"🎯 Smart Router: ZR Express recommended for {dest_wilaya} (southern coverage)")
                return CarrierRecommendation(
                    carrier_type="zr_express",
                    carrier_name="ZR Express",
                    confidence=0.95,
                    reason=f"📍 {dest_wilaya} est dans le Sud - ZR Express a la meilleure couverture",
                    estimated_days=3,
                    rules_applied=rules_applied
                )
            else:
                rules_applied.append("Fallback: ZR Express non configuré")
        
        # Check if destination is in Yalidine territory (northern Algeria)
        if self._check_wilaya_match(dest_wilaya, self.YALIDINE_WILAYAS):
            rules_applied.append("Règle Géographique: Wilaya du Nord")
            
            if 'yalidine' in active_types:
                logger.info(f"🎯 Smart Router: Yalidine recommended for {dest_wilaya} (northern coverage)")
                return CarrierRecommendation(
                    carrier_type="yalidine",
                    carrier_name="Yalidine",
                    confidence=0.90,
                    reason=f"📍 {dest_wilaya} est dans le Nord - Yalidine optimal",
                    estimated_days=2,
                    rules_applied=rules_applied
                )
        
        # ===== RULE 2: Default Fallback =====
        rules_applied.append("Règle par Défaut")
        
        # Try Yalidine first (most common), then ZR Express
        if 'yalidine' in active_types:
            logger.info(f"🎯 Smart Router: Yalidine (default) for {dest_wilaya}")
            return CarrierRecommendation(
                carrier_type="yalidine",
                carrier_name="Yalidine",
                confidence=0.75,
                reason=f"📦 Yalidine sélectionné (transporteur par défaut)",
                estimated_days=2,
                is_fallback=True,
                rules_applied=rules_applied
            )
        
        if 'zr_express' in active_types:
            logger.info(f"🎯 Smart Router: ZR Express (fallback) for {dest_wilaya}")
            return CarrierRecommendation(
                carrier_type="zr_express",
                carrier_name="ZR Express",
                confidence=0.70,
                reason=f"📦 ZR Express sélectionné (fallback)",
                estimated_days=3,
                is_fallback=True,
                rules_applied=rules_applied
            )
        
        # No carrier available
        logger.warning(f"⚠️ Smart Router: No carrier available for user {user_id}")
        return CarrierRecommendation(
            carrier_type="",
            carrier_name="",
            confidence=0.0,
            reason="❌ Aucun transporteur configuré",
            is_fallback=True,
            rules_applied=["Aucun transporteur actif"]
        )
    
    async def get_active_carriers(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active carrier configurations for a user"""
        configs = await self.db.carrier_configs.find(
            {"user_id": user_id, "is_active": True},
            {"_id": 0}
        ).to_list(100)
        return configs
    
    async def get_carrier_instance(self, carrier_type: str, user_id: str) -> Optional[BaseCarrier]:
        """Get an initialized carrier instance for a user"""
        # Get carrier config
        config = await self.db.carrier_configs.find_one(
            {"user_id": user_id, "carrier_type": carrier_type, "is_active": True},
            {"_id": 0}
        )
        
        if not config:
            # For ZR Express mock, create instance without config
            if carrier_type == "zr_express":
                return ZRExpressCarrier({}, test_mode=True)
            logger.warning(f"⚠️ No active config found for {carrier_type}")
            return None
        
        # Get carrier class
        carrier_class = self.CARRIER_CLASSES.get(carrier_type)
        if not carrier_class:
            logger.warning(f"⚠️ Carrier class not implemented: {carrier_type}")
            return None
        
        # Instantiate carrier
        credentials = config.get('credentials', {})
        test_mode = config.get('test_mode', True)
        
        return carrier_class(credentials, test_mode)
    
    async def smart_ship(
        self,
        order: Dict[str, Any],
        user_id: str
    ) -> Tuple[ShipmentResponse, CarrierRecommendation]:
        """
        🚀 Smart Ship - AI-powered shipping
        
        Automatically selects the best carrier and ships the order.
        
        Returns:
            Tuple of (ShipmentResponse, CarrierRecommendation)
        """
        # Get AI recommendation
        recommendation = await self.recommend_carrier(order, user_id)
        
        if not recommendation.carrier_type:
            return (
                ShipmentResponse(
                    success=False,
                    carrier_name="",
                    error_message=recommendation.reason
                ),
                recommendation
            )
        
        # Ship with recommended carrier
        response = await self.sync_order(order, recommendation.carrier_type, user_id)
        
        return (response, recommendation)
    
    async def sync_order(
        self,
        order: Dict[str, Any],
        carrier_type: str,
        user_id: str
    ) -> ShipmentResponse:
        """
        Synchronize an order with a carrier (create shipment)
        """
        try:
            # Get carrier instance
            carrier = await self.get_carrier_instance(carrier_type, user_id)
            
            if not carrier:
                return ShipmentResponse(
                    success=False,
                    carrier_name=carrier_type,
                    error_message=f"Transporteur {carrier_type} non configuré ou inactif"
                )
            
            logger.info(f"📤 Syncing order {order.get('tracking_id')} to {carrier_type}")
            
            # Create shipment with carrier
            response = await carrier.create_shipment(order)
            
            if response.success:
                # Update order in database with carrier info
                await self.db.orders.update_one(
                    {"id": order.get('id')},
                    {
                        "$set": {
                            "carrier_type": carrier_type,
                            "carrier_tracking_id": response.carrier_tracking_id,
                            "carrier_synced_at": datetime.now(timezone.utc).isoformat(),
                            "carrier_label_url": response.label_url,
                            "status": "ready_to_ship",
                            "smart_routed": True,
                            "routing_reason": f"AI: {carrier_type}"
                        }
                    }
                )
                
                logger.info(f"✅ Order synced successfully: {response.carrier_tracking_id}")
            else:
                logger.error(f"❌ Sync failed: {response.error_message}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error syncing order: {str(e)}")
            return ShipmentResponse(
                success=False,
                carrier_name=carrier_type,
                error_message=str(e)
            )
    
    async def select_best_carrier(
        self,
        order: Dict[str, Any],
        user_id: str,
        strategy: RoutingStrategy = RoutingStrategy.SMART
    ) -> Optional[Tuple[str, CarrierScore]]:
        """
        Select the best carrier for an order (legacy method)
        Now redirects to recommend_carrier for SMART strategy
        """
        if strategy == RoutingStrategy.SMART:
            rec = await self.recommend_carrier(order, user_id)
            if rec.carrier_type:
                return (rec.carrier_type, CarrierScore(
                    carrier_type=rec.carrier_type,
                    carrier_name=rec.carrier_name,
                    score=rec.confidence * 100,
                    reason=rec.reason
                ))
            return None
        
        # Fallback to old logic for other strategies
        active_configs = await self.get_active_carriers(user_id)
        if not active_configs:
            return None
        
        # Simple priority-based selection
        for carrier_type in self.DEFAULT_PRIORITY:
            if any(c.get('carrier_type') == carrier_type for c in active_configs):
                return (carrier_type, CarrierScore(
                    carrier_type=carrier_type,
                    carrier_name=carrier_type.replace('_', ' ').title(),
                    score=80,
                    reason=f"Priorité #{self.DEFAULT_PRIORITY.index(carrier_type)+1}"
                ))
        
        return None
    
    async def auto_route_and_sync(
        self,
        order: Dict[str, Any],
        user_id: str,
        strategy: RoutingStrategy = RoutingStrategy.SMART
    ) -> ShipmentResponse:
        """
        Automatically select best carrier and sync order
        """
        response, recommendation = await self.smart_ship(order, user_id)
        return response


# Singleton instance
_router_instance: Optional[SmartRouter] = None

def get_router() -> SmartRouter:
    """Get or create router singleton"""
    global _router_instance
    if _router_instance is None:
        _router_instance = SmartRouter()
    return _router_instance
