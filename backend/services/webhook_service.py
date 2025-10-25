"""
WhatsApp Webhook Service
Handles incoming messages and status updates from Twilio
"""
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for processing WhatsApp webhooks from Twilio"""
    
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
            logger.info("✅ WebhookService MongoDB connection established")
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number by removing whatsapp: prefix"""
        if phone.startswith("whatsapp:"):
            phone = phone.replace("whatsapp:", "")
        if not phone.startswith("+"):
            phone = f"+{phone}"
        return phone
    
    async def process_incoming_message(
        self,
        sender_phone: str,
        recipient_phone: str,
        message_body: str,
        message_sid: str
    ) -> Dict:
        """
        Process an incoming WhatsApp message and store it in MongoDB
        
        Args:
            sender_phone: Customer phone number (From)
            recipient_phone: Business phone number (To)
            message_body: Message text content (Body)
            message_sid: Twilio message SID (MessageSid)
            
        Returns:
            Dict with processing result
        """
        await self.connect()
        
        messages_collection = self.db["whatsapp_messages"]
        conversations_collection = self.db["whatsapp_conversations"]
        
        # Normalize phone numbers
        sender_phone = self._normalize_phone(sender_phone)
        recipient_phone = self._normalize_phone(recipient_phone)
        
        # Create conversation ID
        conversation_id = f"conv_{sender_phone.replace('+', '')}"
        
        # Create message document
        message_doc = {
            "id": message_sid,
            "message_sid": message_sid,
            "conversation_id": conversation_id,
            "sender_phone": sender_phone,
            "recipient_phone": recipient_phone,
            "body": message_body,
            "direction": "inbound",
            "status": "received",
            "timestamp": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "metadata": {}
        }
        
        try:
            # Insert message
            await messages_collection.insert_one(message_doc)
            logger.info(f"✅ Stored incoming message from {sender_phone}: {message_body[:50]}...")
            
            # Update or create conversation
            await conversations_collection.update_one(
                {"conversation_id": conversation_id},
                {
                    "$set": {
                        "customer_phone": sender_phone,
                        "last_message_at": datetime.now(timezone.utc),
                        "is_active": True,
                        "updated_at": datetime.now(timezone.utc)
                    },
                    "$inc": {
                        "message_count": 1,
                        "unread_count": 1
                    },
                    "$setOnInsert": {
                        "id": conversation_id,
                        "conversation_id": conversation_id,
                        "status": "ai_handling",
                        "assigned_agent": None,
                        "customer_name": None,
                        "created_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            
            logger.info(f"✅ Updated conversation {conversation_id}")
            
            return {
                "success": True,
                "message_id": message_sid,
                "conversation_id": conversation_id,
                "message_stored": True
            }
        
        except Exception as e:
            logger.error(f"❌ Error processing incoming message: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_message_status(
        self,
        message_sid: str,
        status: str
    ) -> Dict:
        """
        Update the delivery status of a sent message
        
        Args:
            message_sid: Twilio message SID
            status: New message status (queued, sent, delivered, read, failed)
            
        Returns:
            Dict with update result
        """
        await self.connect()
        
        messages_collection = self.db["whatsapp_messages"]
        
        try:
            result = await messages_collection.update_one(
                {"message_sid": message_sid},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Updated message {message_sid} status to {status}")
                return {"success": True, "message_sid": message_sid, "status": status}
            else:
                logger.warning(f"⚠️ Message {message_sid} not found for status update")
                return {"success": False, "error": "Message not found"}
        
        except Exception as e:
            logger.error(f"❌ Error updating message status: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> list:
        """
        Retrieve messages for a conversation
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message documents
        """
        await self.connect()
        
        messages_collection = self.db["whatsapp_messages"]
        
        try:
            cursor = messages_collection.find(
                {"conversation_id": conversation_id}
            ).sort("timestamp", -1).limit(limit)
            
            messages = []
            async for message in cursor:
                message["_id"] = str(message["_id"])
                message["timestamp"] = message["timestamp"].isoformat()
                message["created_at"] = message["created_at"].isoformat()
                message["updated_at"] = message["updated_at"].isoformat()
                messages.append(message)
            
            # Return in chronological order
            return list(reversed(messages))
        
        except Exception as e:
            logger.error(f"Error retrieving conversation messages: {str(e)}")
            return []
    
    async def mark_conversation_read(self, conversation_id: str) -> bool:
        """Mark all messages in a conversation as read"""
        await self.connect()
        
        conversations_collection = self.db["whatsapp_conversations"]
        
        try:
            await conversations_collection.update_one(
                {"conversation_id": conversation_id},
                {
                    "$set": {
                        "unread_count": 0,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error marking conversation as read: {str(e)}")
            return False

# Singleton instance
webhook_service = WebhookService()
