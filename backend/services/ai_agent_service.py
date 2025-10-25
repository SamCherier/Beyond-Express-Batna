"""
AI Agent Service
Handles conversational AI using GPT-4o via Emergent LLM Key
"""
from emergentintegrations.llm.chat import LlmChat, UserMessage
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import logging
import re
from typing import Dict, Optional, Tuple

from services.order_query_service import order_query_service
from utils.ai_prompts import (
    get_system_prompt,
    INTENT_DETECTION_PROMPT,
    EXTRACT_TRACKING_ID_PROMPT,
    CONFIRMATION_KEYWORDS,
    CANCELLATION_KEYWORDS,
    TRANSFER_KEYWORDS,
    GREETING_KEYWORDS
)

logger = logging.getLogger(__name__)

class AIAgentService:
    """Service for AI-powered WhatsApp conversation handling"""
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'beyond_express_db')
        self.client = None
        self.db = None
        
        if not self.api_key:
            logger.error("❌ EMERGENT_LLM_KEY not configured!")
        else:
            logger.info("✅ AI Agent initialized with Emergent LLM Key")
    
    async def connect(self):
        """Initialize MongoDB connection"""
        if not self.client:
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
    
    def _detect_language(self, message: str) -> str:
        """
        Detect message language (simplified)
        
        Args:
            message: User message text
            
        Returns:
            Language code: 'fr', 'ar', or 'en'
        """
        # Arabic detection (basic - checks for Arabic characters)
        arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F]')
        if arabic_pattern.search(message):
            return 'ar'
        
        # English detection (basic - common English words)
        english_words = ['hello', 'hi', 'order', 'track', 'where', 'status', 'my']
        message_lower = message.lower()
        if any(word in message_lower for word in english_words):
            return 'en'
        
        # Default to French for Algeria
        return 'fr'
    
    def _detect_intent_simple(self, message: str) -> str:
        """
        Detect user intent using keyword matching (fast fallback)
        
        Args:
            message: User message text
            
        Returns:
            Intent: 'tracking', 'confirmation', 'cancellation', 'transfer', 'greeting', 'other'
        """
        message_lower = message.lower()
        
        # Greeting
        if any(keyword in message_lower for keyword in GREETING_KEYWORDS):
            return 'greeting'
        
        # Confirmation
        if any(keyword in message_lower for keyword in CONFIRMATION_KEYWORDS):
            return 'confirmation'
        
        # Cancellation
        if any(keyword in message_lower for keyword in CANCELLATION_KEYWORDS):
            return 'cancellation'
        
        # Transfer to human
        if any(keyword in message_lower for keyword in TRANSFER_KEYWORDS):
            return 'transfer'
        
        # Tracking keywords
        tracking_keywords = ['track', 'suivi', 'où', 'where', 'status', 'statut', 'commande', 'order', 'trk', 'تتبع']
        if any(keyword in message_lower for keyword in tracking_keywords):
            return 'tracking'
        
        return 'other'
    
    def _extract_tracking_id_regex(self, message: str) -> Optional[str]:
        """
        Extract tracking ID using regex (fast fallback)
        
        Args:
            message: User message text
            
        Returns:
            Tracking ID or None
        """
        # Look for TRK followed by digits
        trk_pattern = re.compile(r'TRK\d{6,}', re.IGNORECASE)
        match = trk_pattern.search(message)
        if match:
            return match.group(0).upper()
        
        # Look for order ID pattern ORD-xxxx or TEST-xxxx
        ord_pattern = re.compile(r'(ORD|TEST)-\d{4,}', re.IGNORECASE)
        match = ord_pattern.search(message)
        if match:
            return match.group(0).upper()
        
        # Look for any 6+ digit number
        digit_pattern = re.compile(r'\d{6,}')
        match = digit_pattern.search(message)
        if match:
            return f"TRK{match.group(0)}"
        
        return None
    
    async def _get_or_create_ai_context(self, conversation_id: str, customer_phone: str) -> Dict:
        """
        Get or create AI context for conversation
        
        Args:
            conversation_id: Conversation ID
            customer_phone: Customer phone number
            
        Returns:
            AI context document
        """
        await self.connect()
        
        ai_context_collection = self.db["ai_contexts"]
        
        # Try to find existing context
        context = await ai_context_collection.find_one(
            {"conversation_id": conversation_id},
            {"_id": 0}
        )
        
        if context:
            return context
        
        # Create new context
        new_context = {
            "conversation_id": conversation_id,
            "customer_phone": customer_phone,
            "last_intent": None,
            "order_references": [],
            "language": "fr",
            "context_data": {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await ai_context_collection.insert_one(new_context.copy())
        logger.info(f"✅ Created new AI context for conversation: {conversation_id}")
        
        return new_context
    
    async def _update_ai_context(self, conversation_id: str, updates: Dict):
        """Update AI context with new information"""
        await self.connect()
        
        ai_context_collection = self.db["ai_contexts"]
        
        updates["updated_at"] = datetime.now(timezone.utc)
        
        await ai_context_collection.update_one(
            {"conversation_id": conversation_id},
            {"$set": updates}
        )
    
    async def process_message_and_respond(
        self,
        conversation_id: str,
        customer_phone: str,
        message: str
    ) -> Tuple[str, bool]:
        """
        Process incoming message and generate AI response
        
        Args:
            conversation_id: Conversation ID
            customer_phone: Customer phone number
            message: User message text
            
        Returns:
            Tuple of (AI response text, should_transfer_to_human)
        """
        if not self.api_key:
            return ("Désolé, le service IA n'est pas disponible pour le moment. Un agent va vous contacter.", True)
        
        try:
            # Get or create AI context
            context = await self._get_or_create_ai_context(conversation_id, customer_phone)
            
            # Detect language
            language = self._detect_language(message)
            await self._update_ai_context(conversation_id, {"language": language})
            
            # Detect intent
            intent = self._detect_intent_simple(message)
            await self._update_ai_context(conversation_id, {"last_intent": intent})
            
            logger.info(f"📊 Intent detected: {intent} | Language: {language}")
            
            # Handle specific intents
            if intent == 'transfer':
                return ("Je vous transfère vers un agent humain qui pourra mieux vous aider. Un instant s'il vous plaît! 👤", True)
            
            elif intent == 'greeting':
                greeting_response = self._get_greeting_response(language)
                return (greeting_response, False)
            
            elif intent == 'tracking':
                # Extract tracking ID
                tracking_id = self._extract_tracking_id_regex(message)
                
                if tracking_id:
                    # Query order information
                    order = await order_query_service.find_order_by_tracking_id(tracking_id)
                    
                    if not order:
                        # Try by order ID
                        order = await order_query_service.find_order_by_id(tracking_id)
                    
                    if order:
                        # Format order info
                        order_info = order_query_service.format_order_info(order)
                        
                        # Store order reference in context
                        await self._update_ai_context(
                            conversation_id,
                            {"order_references": [order["id"]]}
                        )
                        
                        response = f"🔍 J'ai trouvé votre commande!\n\n{order_info}\n\nAutre chose que je puisse faire pour vous? 😊"
                        return (response, False)
                    else:
                        response = f"❌ Je n'ai pas trouvé de commande avec le numéro {tracking_id}.\n\nVérifiez le numéro ou contactez-nous pour plus d'aide. 📞"
                        return (response, False)
                else:
                    # Ask for tracking ID
                    response = "Pour suivre votre commande, envoyez-moi votre numéro de suivi (ex: TRK123456). 📦"
                    return (response, False)
            
            elif intent == 'confirmation':
                # Check if there's a pending order in context
                order_refs = context.get("order_references", [])
                if order_refs:
                    last_order_id = order_refs[-1]
                    success = await order_query_service.confirm_order(last_order_id)
                    
                    if success:
                        response = f"✅ Parfait! Votre commande #{last_order_id} est confirmée.\n\nNous allons la préparer et l'envoyer rapidement. Merci! 🚀"
                        return (response, False)
                    else:
                        response = "❌ Désolé, je n'ai pas pu confirmer la commande. Un agent va vous contacter."
                        return (response, True)
                else:
                    response = "Je ne trouve pas de commande à confirmer. Pouvez-vous m'envoyer votre numéro de suivi? 📦"
                    return (response, False)
            
            elif intent == 'cancellation':
                # Check if there's a pending order in context
                order_refs = context.get("order_references", [])
                if order_refs:
                    last_order_id = order_refs[-1]
                    success = await order_query_service.cancel_order(last_order_id, "Client request via WhatsApp")
                    
                    if success:
                        response = f"✅ Votre commande #{last_order_id} a été annulée.\n\nSi vous avez des questions, n'hésitez pas à nous contacter. 📞"
                        return (response, False)
                    else:
                        response = "❌ Je n'ai pas pu annuler la commande. Un agent va vous contacter pour traiter votre demande."
                        return (response, True)
                else:
                    response = "Quelle commande souhaitez-vous annuler? Envoyez-moi le numéro de suivi. 📦"
                    return (response, False)
            
            # For other intents, use GPT-4o
            return await self._generate_ai_response(conversation_id, customer_phone, message, language, context)
        
        except Exception as e:
            logger.error(f"❌ Error processing message: {str(e)}")
            return ("Désolé, une erreur s'est produite. Un agent va vous contacter.", True)
    
    def _get_greeting_response(self, language: str) -> str:
        """Get greeting response based on language"""
        if language == 'ar':
            return "مرحبا! 👋 أنا مساعد Beyond Express.\n\nكيف يمكنني مساعدتك اليوم؟"
        elif language == 'en':
            return "Hello! 👋 I'm the Beyond Express assistant.\n\nHow can I help you today?"
        else:
            return "Bonjour! 👋 Je suis l'assistant Beyond Express.\n\nComment puis-je vous aider aujourd'hui?"
    
    async def _generate_ai_response(
        self,
        conversation_id: str,
        customer_phone: str,
        message: str,
        language: str,
        context: Dict
    ) -> Tuple[str, bool]:
        """
        Generate AI response using GPT-4o
        
        Args:
            conversation_id: Conversation ID
            customer_phone: Customer phone
            message: User message
            language: Detected language
            context: AI context
            
        Returns:
            Tuple of (AI response, should_transfer)
        """
        try:
            # Create LlmChat instance for this conversation
            chat = LlmChat(
                api_key=self.api_key,
                session_id=conversation_id,
                system_message=get_system_prompt(language)
            )
            
            # Use GPT-4o model
            chat.with_model("openai", "gpt-4o")
            
            # Create user message
            user_message = UserMessage(text=message)
            
            # Send message and get response
            response = await chat.send_message(user_message)
            
            logger.info(f"✅ GPT-4o response generated for conversation: {conversation_id}")
            
            # Check if AI wants to transfer to human
            should_transfer = any(keyword in response.lower() for keyword in ["transférer", "transfer", "agent humain"])
            
            return (response, should_transfer)
        
        except Exception as e:
            logger.error(f"❌ Error generating AI response: {str(e)}")
            return ("Désolé, je rencontre un problème. Un agent va vous contacter. 👤", True)

# Singleton instance
ai_agent_service = AIAgentService()
