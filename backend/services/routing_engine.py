"""
Smart Routing Engine
Intelligent carrier selection and order synchronization

Features:
  - Automatic carrier selection based on cost, speed, coverage
  - Order synchronization with carrier APIs
  - Multi-carrier support
  - Fallback handling
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorClient
import os

from .carriers.base import BaseCarrier, ShipmentResponse
from .carriers.yalidine import YalidineCarrier

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Strategy for selecting carrier"""
    CHEAPEST = "cheapest"  # Select lowest cost carrier
    FASTEST = "fastest"    # Select fastest delivery carrier
    PRIORITY = "priority"  # Use configured priority order
    COVERAGE = "coverage"  # Best coverage for destination
    BALANCED = "balanced"  # Balance cost and speed


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
    Smart Routing Engine
    
    Intelligently selects the best carrier for each order based on:
    - Cost optimization
    - Delivery speed
    - Coverage/availability
    - User preferences
    - Historical performance
    """
    
    # Carrier classes registry
    CARRIER_CLASSES = {
        "yalidine": YalidineCarrier,
        # Add more carriers here as they are implemented:
        # "dhd": DHDCarrier,
        # "zr_express": ZRExpressCarrier,
        # "maystro": MaystroCarrier,
    }
    
    # Default carrier priority (can be overridden per user)
    DEFAULT_PRIORITY = ["yalidine", "dhd", "zr_express", "maystro", "guepex"]
    
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'beyond_express_db')
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.db_name]
        
        logger.info("🧠 SmartRouter initialized")
    
    async def get_active_carriers(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active carrier configurations for a user
        """
        configs = await self.db.carrier_configs.find(
            {"user_id": user_id, "is_active": True},
            {"_id": 0}
        ).to_list(100)
        
        return configs
    
    async def get_carrier_instance(self, carrier_type: str, user_id: str) -> Optional[BaseCarrier]:
        """
        Get an initialized carrier instance for a user
        """
        # Get carrier config
        config = await self.db.carrier_configs.find_one(
            {"user_id": user_id, "carrier_type": carrier_type, "is_active": True},
            {"_id": 0}
        )
        
        if not config:
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
    
    async def select_best_carrier(
        self,
        order: Dict[str, Any],
        user_id: str,
        strategy: RoutingStrategy = RoutingStrategy.PRIORITY
    ) -> Optional[Tuple[str, CarrierScore]]:
        """
        Select the best carrier for an order
        
        Args:
            order: Order data from database
            user_id: User ID to get carrier configs
            strategy: Selection strategy to use
            
        Returns:
            Tuple of (carrier_type, CarrierScore) or None if no carrier available
        """
        try:
            # Get active carriers for user
            active_configs = await self.get_active_carriers(user_id)
            
            if not active_configs:
                logger.warning(f"⚠️ No active carriers for user {user_id}")
                return None
            
            recipient = order.get('recipient', {})
            dest_wilaya = recipient.get('wilaya', '')
            
            scores: List[CarrierScore] = []
            
            for config in active_configs:
                carrier_type = config.get('carrier_type')
                carrier_name = config.get('carrier_name', carrier_type)
                
                # Get carrier instance
                carrier = await self.get_carrier_instance(carrier_type, user_id)
                if not carrier:
                    continue
                
                # Calculate score based on strategy
                score = await self._calculate_carrier_score(
                    carrier, carrier_type, carrier_name, order, strategy
                )
                
                if score:
                    scores.append(score)
            
            if not scores:
                logger.warning("⚠️ No carriers scored for order")
                return None
            
            # Sort by score (highest first)
            scores.sort(key=lambda x: x.score, reverse=True)
            
            best = scores[0]
            logger.info(f"🎯 Best carrier for order: {best.carrier_name} (score: {best.score:.2f}, reason: {best.reason})")
            
            return (best.carrier_type, best)
            
        except Exception as e:
            logger.error(f"❌ Error selecting carrier: {str(e)}")
            return None
    
    async def _calculate_carrier_score(
        self,
        carrier: BaseCarrier,
        carrier_type: str,
        carrier_name: str,
        order: Dict[str, Any],
        strategy: RoutingStrategy
    ) -> Optional[CarrierScore]:
        """
        Calculate score for a carrier based on strategy
        """
        try:
            recipient = order.get('recipient', {})
            sender = order.get('sender', {})
            
            origin = sender.get('wilaya', 'Batna')
            dest = recipient.get('wilaya', '')
            
            # Get rate if possible
            cost = await carrier.get_rates(origin, dest)
            
            if strategy == RoutingStrategy.CHEAPEST:
                # Score based on cost (lower cost = higher score)
                if cost:
                    score = 1000 / max(cost, 1)
                else:
                    score = 50  # Default medium score if cost unknown
                reason = f"Coût: {cost or 'N/A'} DZD"
                
            elif strategy == RoutingStrategy.FASTEST:
                # Score based on estimated speed (hardcoded for now)
                speed_scores = {
                    "yalidine": 90,
                    "dhd": 85,
                    "zr_express": 80,
                    "maystro": 75,
                }
                score = speed_scores.get(carrier_type, 70)
                reason = "Livraison rapide"
                
            elif strategy == RoutingStrategy.PRIORITY:
                # Score based on configured priority
                priority_order = self.DEFAULT_PRIORITY
                if carrier_type in priority_order:
                    position = priority_order.index(carrier_type)
                    score = 100 - (position * 10)
                else:
                    score = 50
                reason = f"Priorité #{priority_order.index(carrier_type)+1 if carrier_type in priority_order else 'N/A'}"
                
            elif strategy == RoutingStrategy.BALANCED:
                # Balance cost and speed
                cost_score = 1000 / max(cost, 1) if cost else 50
                speed_scores = {"yalidine": 90, "dhd": 85, "zr_express": 80}
                speed_score = speed_scores.get(carrier_type, 70)
                score = (cost_score + speed_score) / 2
                reason = f"Équilibré (coût: {cost or 'N/A'} DZD)"
                
            else:
                score = 50
                reason = "Score par défaut"
            
            return CarrierScore(
                carrier_type=carrier_type,
                carrier_name=carrier_name,
                score=score,
                cost=cost,
                reason=reason
            )
            
        except Exception as e:
            logger.error(f"❌ Error calculating score for {carrier_type}: {str(e)}")
            return None
    
    async def sync_order(
        self,
        order: Dict[str, Any],
        carrier_type: str,
        user_id: str
    ) -> ShipmentResponse:
        """
        Synchronize an order with a carrier (create shipment)
        
        Args:
            order: Order data from database
            carrier_type: Carrier to use (e.g., 'yalidine')
            user_id: User ID for carrier config
            
        Returns:
            ShipmentResponse with result
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
                            "carrier_synced_at": datetime.now().isoformat(),
                            "carrier_label_url": response.label_url,
                            "status": "ready_to_ship"
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
    
    async def auto_route_and_sync(
        self,
        order: Dict[str, Any],
        user_id: str,
        strategy: RoutingStrategy = RoutingStrategy.PRIORITY
    ) -> ShipmentResponse:
        """
        Automatically select best carrier and sync order
        
        This is the "magic button" that does everything:
        1. Analyzes order
        2. Selects best carrier
        3. Creates shipment
        4. Returns tracking info
        """
        # Select best carrier
        result = await self.select_best_carrier(order, user_id, strategy)
        
        if not result:
            return ShipmentResponse(
                success=False,
                carrier_name="",
                error_message="Aucun transporteur disponible. Veuillez configurer au moins un transporteur."
            )
        
        carrier_type, score = result
        
        # Sync order with selected carrier
        response = await self.sync_order(order, carrier_type, user_id)
        
        return response


# Singleton instance
from datetime import datetime
_router_instance: Optional[SmartRouter] = None

def get_router() -> SmartRouter:
    """Get or create router singleton"""
    global _router_instance
    if _router_instance is None:
        _router_instance = SmartRouter()
    return _router_instance
