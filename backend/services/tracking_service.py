"""
Tracking Service - Unified Status Synchronization
Syncs order statuses from all carriers and normalizes them

Features:
  - Multi-carrier status sync (Yalidine, ZR Express, DHD)
  - Status normalization to Master Statuses
  - Timeline event generation
  - Mock progression for demo/testing
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid

from .status_mapper import (
    MasterStatus, normalize_status, get_status_meta,
    get_next_status_simulation, is_final_status,
    get_status_label, get_status_icon
)
from .routing_engine import get_router

logger = logging.getLogger(__name__)


class TrackingService:
    """
    Unified Tracking Service
    
    Handles status synchronization across all carriers
    and maintains a unified tracking timeline
    """
    
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'beyond_express_db')
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.db_name]
        
        logger.info("🔄 TrackingService initialized")
    
    async def sync_order_status(
        self,
        order_id: str,
        user_id: str,
        force_advance: bool = False
    ) -> Dict[str, Any]:
        """
        Sync status for a single order from its carrier
        
        Args:
            order_id: Order ID to sync
            user_id: User ID for carrier config access
            force_advance: For ZR Mock - force status to advance (demo)
            
        Returns:
            Dict with sync result including old/new status
        """
        try:
            # Get order
            order = await self.db.orders.find_one(
                {"id": order_id},
                {"_id": 0}
            )
            
            if not order:
                return {
                    "success": False,
                    "order_id": order_id,
                    "error": "Commande non trouvée"
                }
            
            carrier_type = order.get('carrier_type', '')
            carrier_tracking = order.get('carrier_tracking_id', '')
            current_status = order.get('status', 'pending')
            
            # If no carrier assigned, nothing to sync
            if not carrier_type or not carrier_tracking:
                return {
                    "success": True,
                    "order_id": order_id,
                    "carrier_type": None,
                    "status_changed": False,
                    "message": "Pas de transporteur assigné"
                }
            
            logger.info(f"🔄 Syncing status for {order_id} via {carrier_type}")
            
            # Get carrier instance
            router = get_router()
            carrier = await router.get_carrier_instance(carrier_type, user_id)
            
            new_status = current_status
            carrier_raw_status = None
            location = None
            
            if carrier:
                # Special handling for ZR Express Mock
                if carrier_type == "zr_express" and hasattr(carrier, 'is_mock') and carrier.is_mock:
                    # Simulate status progression for demo
                    result = await self._simulate_zr_progress(order, force_advance)
                    new_status = result['new_status']
                    carrier_raw_status = result['carrier_raw_status']
                    location = result.get('location')
                else:
                    # Real carrier - fetch tracking info
                    tracking_updates = await carrier.get_tracking(carrier_tracking)
                    
                    if tracking_updates:
                        latest = tracking_updates[-1]  # Most recent update
                        carrier_raw_status = latest.description or latest.carrier_status_code
                        location = latest.location
                        
                        # Normalize to our status
                        normalized = normalize_status(carrier_raw_status, carrier_type)
                        new_status = normalized.value
            else:
                # No carrier instance available
                return {
                    "success": True,
                    "order_id": order_id,
                    "carrier_type": carrier_type,
                    "status_changed": False,
                    "message": f"Transporteur {carrier_type} non configuré"
                }
            
            # Check if status changed
            status_changed = new_status != current_status
            
            if status_changed:
                # Update order status
                update_data = {
                    "status": new_status,
                    "last_sync_at": datetime.now(timezone.utc).isoformat(),
                    "last_carrier_status": carrier_raw_status
                }
                
                # Handle special statuses
                if new_status == MasterStatus.DELIVERED.value:
                    update_data["delivered_at"] = datetime.now(timezone.utc).isoformat()
                    update_data["payment_status"] = "collected_by_driver"
                elif new_status == MasterStatus.RETURNED.value:
                    update_data["returned_at"] = datetime.now(timezone.utc).isoformat()
                    update_data["payment_status"] = "returned"
                
                await self.db.orders.update_one(
                    {"id": order_id},
                    {"$set": update_data}
                )
                
                # Add tracking event
                await self._add_tracking_event(
                    order_id=order_id,
                    status=new_status,
                    carrier_status=carrier_raw_status,
                    carrier_type=carrier_type,
                    location=location
                )
                
                logger.info(f"✅ Status updated: {current_status} -> {new_status}")
            
            # Get status metadata
            status_enum = MasterStatus(new_status) if new_status in [s.value for s in MasterStatus] else MasterStatus.PENDING
            status_meta = get_status_meta(status_enum)
            
            return {
                "success": True,
                "order_id": order_id,
                "tracking_id": order.get('tracking_id'),
                "carrier_type": carrier_type,
                "carrier_tracking_id": carrier_tracking,
                "carrier_raw_status": carrier_raw_status,
                "old_status": current_status,
                "new_status": new_status,
                "status_changed": status_changed,
                "status_label": status_meta["label"],
                "status_icon": status_meta["icon"],
                "status_color": status_meta["color"],
                "location": location,
                "synced_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error syncing order {order_id}: {str(e)}")
            return {
                "success": False,
                "order_id": order_id,
                "error": str(e)
            }
    
    async def _simulate_zr_progress(
        self,
        order: Dict[str, Any],
        force_advance: bool
    ) -> Dict[str, Any]:
        """
        🚀 TIME TRAVEL - Simulate ZR Express status progression for demo
        
        SIMPLIFIED progression (per user request):
        - 1st click: PENDING/any -> IN_TRANSIT
        - 2nd click: IN_TRANSIT -> DELIVERED
        - After DELIVERED: stays DELIVERED
        
        This allows quick demo without waiting for real trucks!
        """
        current_status = order.get('status', 'pending')
        
        logger.info(f"🕐 Time Travel activated! Current: {current_status}")
        
        # TIME TRAVEL LOGIC - Simple 3-step progression
        # pending/preparing/ready_to_ship -> in_transit -> delivered
        
        if current_status in ['pending', 'preparing', 'ready_to_ship', 'picked_up', 'in_stock']:
            # First click: Jump to IN_TRANSIT
            next_status = 'in_transit'
            location = f"Hub ZR Express - En route vers {order.get('recipient', {}).get('wilaya', 'destination')}"
            carrier_raw = "IN_TRANSIT"
            
        elif current_status == 'in_transit':
            # Second click: Jump to DELIVERED
            next_status = 'delivered'
            location = f"Livré à {order.get('recipient', {}).get('commune', '')} - {order.get('recipient', {}).get('wilaya', '')}"
            carrier_raw = "DELIVERED"
            
        elif current_status == 'out_for_delivery':
            # Also jump to DELIVERED
            next_status = 'delivered'
            location = f"Livré à {order.get('recipient', {}).get('commune', '')} - {order.get('recipient', {}).get('wilaya', '')}"
            carrier_raw = "DELIVERED"
            
        else:
            # Already delivered/returned/cancelled - no change
            next_status = current_status
            location = None
            carrier_raw = current_status.upper()
        
        logger.info(f"🕐 Time Travel result: {current_status} -> {next_status}")
        
        return {
            "new_status": next_status,
            "carrier_raw_status": carrier_raw,
            "location": location
        }
    
    async def _add_tracking_event(
        self,
        order_id: str,
        status: str,
        carrier_status: Optional[str],
        carrier_type: str,
        location: Optional[str]
    ):
        """Add a tracking event to the database"""
        try:
            status_enum = MasterStatus(status) if status in [s.value for s in MasterStatus] else MasterStatus.PENDING
            
            event = {
                "id": str(uuid.uuid4()),
                "order_id": order_id,
                "status": status,
                "status_label": get_status_label(status_enum),
                "status_icon": get_status_icon(status_enum),
                "carrier_status": carrier_status,
                "carrier_type": carrier_type,
                "location": location,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "carrier_sync"
            }
            
            await self.db.tracking_events.insert_one(event)
            logger.info(f"📝 Tracking event added: {status}")
            
        except Exception as e:
            logger.error(f"❌ Error adding tracking event: {str(e)}")
    
    async def sync_bulk_orders(
        self,
        order_ids: List[str],
        user_id: str,
        force_advance: bool = False
    ) -> Dict[str, Any]:
        """
        Sync status for multiple orders
        
        Args:
            order_ids: List of order IDs to sync
            user_id: User ID for carrier config access
            force_advance: For ZR Mock - force status advancement
            
        Returns:
            Dict with summary and individual results
        """
        results = []
        changed_count = 0
        
        for order_id in order_ids:
            result = await self.sync_order_status(order_id, user_id, force_advance)
            results.append(result)
            
            if result.get('status_changed'):
                changed_count += 1
        
        return {
            "total": len(order_ids),
            "synced": len([r for r in results if r.get('success')]),
            "changed": changed_count,
            "failed": len([r for r in results if not r.get('success')]),
            "results": results
        }
    
    async def get_order_timeline(self, order_id: str) -> List[Dict[str, Any]]:
        """
        Get full tracking timeline for an order
        
        Returns chronological list of tracking events
        """
        try:
            events = await self.db.tracking_events.find(
                {"order_id": order_id},
                {"_id": 0}
            ).sort("timestamp", 1).to_list(100)
            
            # Add status metadata to each event
            for event in events:
                status = event.get('status', 'pending')
                try:
                    status_enum = MasterStatus(status)
                    meta = get_status_meta(status_enum)
                    event['color'] = meta['color']
                    event['bg_color'] = meta['bg_color']
                    event['icon'] = meta['icon']
                except ValueError:
                    event['color'] = '#6B7280'
                    event['bg_color'] = '#F3F4F6'
                    event['icon'] = '📦'
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error getting timeline: {str(e)}")
            return []
    
    async def get_status_summary(self, user_id: str) -> Dict[str, int]:
        """Get count of orders by status for a user"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            
            cursor = self.db.orders.aggregate(pipeline)
            results = await cursor.to_list(100)
            
            return {r['_id']: r['count'] for r in results if r['_id']}
            
        except Exception as e:
            logger.error(f"❌ Error getting status summary: {str(e)}")
            return {}


# Singleton instance
_tracking_service: Optional[TrackingService] = None

def get_tracking_service() -> TrackingService:
    """Get or create tracking service singleton"""
    global _tracking_service
    if _tracking_service is None:
        _tracking_service = TrackingService()
    return _tracking_service
