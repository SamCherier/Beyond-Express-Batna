"""
Order Query Service
Provides database query functions for AI Agent to access order information
"""
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class OrderQueryService:
    """Service for querying order information for AI Agent"""
    
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'beyond_express_db')
        self.client = None
        self.db = None
    
    async def connect(self):
        """Initialize MongoDB connection"""
        if not self.client:
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
            logger.info("✅ OrderQueryService MongoDB connected")
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
    
    async def find_order_by_tracking_id(self, tracking_id: str) -> Optional[Dict]:
        """
        Find an order by tracking ID
        
        Args:
            tracking_id: The tracking ID to search for
            
        Returns:
            Order document or None if not found
        """
        await self.connect()
        
        orders_collection = self.db["orders"]
        
        try:
            order = await orders_collection.find_one(
                {"tracking_id": tracking_id},
                {"_id": 0}
            )
            
            if order:
                logger.info(f"✅ Found order with tracking ID: {tracking_id}")
                return order
            else:
                logger.info(f"❌ No order found with tracking ID: {tracking_id}")
                return None
        
        except Exception as e:
            logger.error(f"Error finding order: {str(e)}")
            return None
    
    async def find_order_by_id(self, order_id: str) -> Optional[Dict]:
        """
        Find an order by order ID
        
        Args:
            order_id: The order ID to search for
            
        Returns:
            Order document or None if not found
        """
        await self.connect()
        
        orders_collection = self.db["orders"]
        
        try:
            order = await orders_collection.find_one(
                {"id": order_id},
                {"_id": 0}
            )
            
            if order:
                logger.info(f"✅ Found order with ID: {order_id}")
                return order
            else:
                logger.info(f"❌ No order found with ID: {order_id}")
                return None
        
        except Exception as e:
            logger.error(f"Error finding order: {str(e)}")
            return None
    
    async def find_orders_by_phone(self, customer_phone: str, limit: int = 5) -> List[Dict]:
        """
        Find recent orders by customer phone number
        
        Args:
            customer_phone: Customer phone number
            limit: Maximum number of orders to return
            
        Returns:
            List of order documents
        """
        await self.connect()
        
        orders_collection = self.db["orders"]
        
        # Normalize phone number
        phone = customer_phone.replace("whatsapp:", "").replace("+", "")
        
        try:
            cursor = orders_collection.find(
                {
                    "$or": [
                        {"recipient.phone": {"$regex": phone}},
                        {"recipient.phone": customer_phone}
                    ]
                },
                {"_id": 0}
            ).sort("created_at", -1).limit(limit)
            
            orders = []
            async for order in cursor:
                orders.append(order)
            
            logger.info(f"✅ Found {len(orders)} orders for phone: {customer_phone}")
            return orders
        
        except Exception as e:
            logger.error(f"Error finding orders by phone: {str(e)}")
            return []
    
    async def get_order_status_history(self, order_id: str) -> List[Dict]:
        """
        Get tracking events (status history) for an order
        
        Args:
            order_id: Order ID
            
        Returns:
            List of tracking events
        """
        await self.connect()
        
        tracking_collection = self.db["tracking_events"]
        
        try:
            cursor = tracking_collection.find(
                {"order_id": order_id},
                {"_id": 0}
            ).sort("timestamp", 1)
            
            events = []
            async for event in cursor:
                events.append(event)
            
            logger.info(f"✅ Found {len(events)} tracking events for order: {order_id}")
            return events
        
        except Exception as e:
            logger.error(f"Error getting tracking history: {str(e)}")
            return []
    
    def format_order_info(self, order: Dict) -> str:
        """
        Format order information for AI response
        
        Args:
            order: Order document
            
        Returns:
            Formatted string with order details
        """
        if not order:
            return "Aucune information de commande disponible."
        
        recipient = order.get("recipient", {})
        status_map = {
            "in_stock": "En stock",
            "preparing": "En préparation",
            "ready_to_ship": "Prêt à expédier",
            "in_transit": "En transit",
            "delivered": "Livré",
            "returned": "Retourné",
            "failed": "Échec"
        }
        
        status = status_map.get(order.get("status", ""), order.get("status", "Inconnu"))
        
        info = f"""📦 Commande #{order.get('id', 'N/A')}
🔢 N° Suivi: {order.get('tracking_id', 'N/A')}
📍 Statut: {status}
👤 Destinataire: {recipient.get('name', 'N/A')}
📞 Téléphone: {recipient.get('phone', 'N/A')}
🏘️ Wilaya: {recipient.get('wilaya', 'N/A')}
🏙️ Commune: {recipient.get('commune', 'N/A')}
💰 Montant: {order.get('cod_amount', 0):,.0f} DA"""
        
        return info
    
    async def confirm_order(self, order_id: str) -> bool:
        """
        Mark an order as confirmed by customer
        
        Args:
            order_id: Order ID to confirm
            
        Returns:
            True if confirmed successfully
        """
        await self.connect()
        
        orders_collection = self.db["orders"]
        
        try:
            result = await orders_collection.update_one(
                {"id": order_id},
                {
                    "$set": {
                        "confirmed": True,
                        "confirmed_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Order {order_id} confirmed by customer")
                return True
            else:
                logger.warning(f"⚠️ Order {order_id} not found for confirmation")
                return False
        
        except Exception as e:
            logger.error(f"Error confirming order: {str(e)}")
            return False
    
    async def cancel_order(self, order_id: str, reason: str = "Customer request") -> bool:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            reason: Cancellation reason
            
        Returns:
            True if cancelled successfully
        """
        await self.connect()
        
        orders_collection = self.db["orders"]
        
        try:
            result = await orders_collection.update_one(
                {"id": order_id},
                {
                    "$set": {
                        "status": "cancelled",
                        "cancellation_reason": reason,
                        "cancelled_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Order {order_id} cancelled: {reason}")
                return True
            else:
                logger.warning(f"⚠️ Order {order_id} not found for cancellation")
                return False
        
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False

# Singleton instance
order_query_service = OrderQueryService()
