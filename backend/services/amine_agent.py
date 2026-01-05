"""
🇩🇿 Amine - The Algerian AI Agent
Beyond Express Support Agent powered by Gemini

Features:
- Multi-language: Darja Algérienne, Français, Arabe
- Function Calling: get_order_status, calculate_price
- Real-time DB queries for order tracking
- Pricing calculator for all 58 wilayas
"""

import google.generativeai as genai
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import logging
import re
import json
from typing import Dict, Optional, Any, List

logger = logging.getLogger(__name__)

# ============================================
# 🇩🇿 AMINE'S PERSONA - System Prompt
# ============================================

AMINE_SYSTEM_PROMPT = """
أنت "أمين" (Amine)، مساعد Beyond Express الذكي. أنت جزائري 🇩🇿 وتتكلم بالدارجة الجزائرية والفرنسية والعربية الفصحى.

## شخصيتك (Personnalité)
- اسمك: أمين
- تعمل في: Beyond Express - شركة لوجستيك جزائرية
- أسلوبك: ودود، محترف، لكن قريب من الناس كأنك صديق
- تستعمل التعبيرات الجزائرية مثل:
  * "مرحبا بيك!" / "Merhba bik!"
  * "ما تخمش راسك" / "Ma tkezerch rassek"
  * "إن شاء الله كل شيء يمشي مليح"
  * "واش راك؟" / "Wach rak?"
  * "كاين مشكل؟ نحلولك!"

## قواعد اللغة
1. إذا كتب المستخدم بالدارجة أو بحروف لاتينية جزائرية (ex: "win rah", "chhal", "kifach") → أجب بالدارجة
2. إذا كتب بالفرنسية → أجب بالفرنسية  
3. إذا كتب بالعربية الفصحى → أجب بالعربية الفصحى
4. استخدم الإيموجي دائماً: 📦 🚚 ✅ 💰 🇩🇿

## الخدمات المتاحة
1. **تتبع الطرود**: "Win rah l'colis?" → استعمل الأداة get_order_status
2. **حساب الأسعار**: "Chhal livraison l'Oran?" → استعمل الأداة calculate_shipping_price
3. **معلومات عامة**: أجب من معرفتك عن Beyond Express

## معلومات Beyond Express
- شركة لوجستيك جزائرية متخصصة في توصيل الطرود
- خدمة الدفع عند الاستلام (COD)
- تغطية كل 58 ولاية جزائرية
- تتبع الطرود بالوقت الحقيقي
- إشعارات واتساب أوتوماتيكية

## مهم جداً
- عند البحث عن طرد، استخرج رقم التتبع من الرسالة (TRK, BEX-, YAL-)
- كن دقيقاً في المعلومات
- إذا لم تجد طرد، اطلب من المستخدم التحقق من الرقم
"""

# ============================================
# 📦 PRICING GRID - All 58 Wilayas
# ============================================

ALGERIA_PRICING = {
    # Zone A - Alger & Proche
    "alger": {"domicile": 400, "stopdesk": 300},
    "blida": {"domicile": 450, "stopdesk": 350},
    "boumerdès": {"domicile": 450, "stopdesk": 350},
    "tipaza": {"domicile": 450, "stopdesk": 350},
    
    # Zone B - Centre
    "bouira": {"domicile": 500, "stopdesk": 400},
    "médéa": {"domicile": 500, "stopdesk": 400},
    "tizi ouzou": {"domicile": 500, "stopdesk": 400},
    "béjaïa": {"domicile": 550, "stopdesk": 450},
    "sétif": {"domicile": 550, "stopdesk": 450},
    "bordj bou arréridj": {"domicile": 550, "stopdesk": 450},
    "m'sila": {"domicile": 550, "stopdesk": 450},
    "jijel": {"domicile": 550, "stopdesk": 450},
    
    # Zone C - Est
    "constantine": {"domicile": 600, "stopdesk": 500},
    "batna": {"domicile": 600, "stopdesk": 500},
    "annaba": {"domicile": 600, "stopdesk": 500},
    "skikda": {"domicile": 600, "stopdesk": 500},
    "guelma": {"domicile": 600, "stopdesk": 500},
    "oum el bouaghi": {"domicile": 600, "stopdesk": 500},
    "khenchela": {"domicile": 600, "stopdesk": 500},
    "tébessa": {"domicile": 650, "stopdesk": 550},
    "souk ahras": {"domicile": 650, "stopdesk": 550},
    "el tarf": {"domicile": 650, "stopdesk": 550},
    "mila": {"domicile": 600, "stopdesk": 500},
    
    # Zone D - Ouest  
    "oran": {"domicile": 550, "stopdesk": 450},
    "mostaganem": {"domicile": 550, "stopdesk": 450},
    "chlef": {"domicile": 500, "stopdesk": 400},
    "relizane": {"domicile": 550, "stopdesk": 450},
    "mascara": {"domicile": 550, "stopdesk": 450},
    "tiaret": {"domicile": 600, "stopdesk": 500},
    "tissemsilt": {"domicile": 600, "stopdesk": 500},
    "sidi bel abbès": {"domicile": 600, "stopdesk": 500},
    "tlemcen": {"domicile": 600, "stopdesk": 500},
    "aïn témouchent": {"domicile": 600, "stopdesk": 500},
    "saïda": {"domicile": 650, "stopdesk": 550},
    
    # Zone E - Sud (Proche)
    "djelfa": {"domicile": 650, "stopdesk": 550},
    "laghouat": {"domicile": 700, "stopdesk": 600},
    "biskra": {"domicile": 700, "stopdesk": 600},
    "el oued": {"domicile": 750, "stopdesk": 650},
    "ouargla": {"domicile": 800, "stopdesk": 700},
    "ghardaïa": {"domicile": 800, "stopdesk": 700},
    
    # Zone F - Grand Sud
    "béchar": {"domicile": 900, "stopdesk": 800},
    "naâma": {"domicile": 850, "stopdesk": 750},
    "el bayadh": {"domicile": 850, "stopdesk": 750},
    "adrar": {"domicile": 1000, "stopdesk": 900},
    "tindouf": {"domicile": 1200, "stopdesk": 1100},
    "tamanrasset": {"domicile": 1200, "stopdesk": 1100},
    "illizi": {"domicile": 1200, "stopdesk": 1100},
    
    # Wilayas restantes
    "aïn defla": {"domicile": 500, "stopdesk": 400},
    "djelfa": {"domicile": 650, "stopdesk": 550},
}

# Default pricing for unlisted wilayas
DEFAULT_PRICING = {"domicile": 700, "stopdesk": 600}


class AmineAgent:
    """
    Amine - The Algerian AI Agent for Beyond Express
    
    Powered by Google Gemini with Function Calling
    """
    
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'beyond_express_db')
        self.client = None
        self.db = None
        
        # Define tools for function calling
        self.tools = self._define_tools()
        
        logger.info("🇩🇿 Amine Agent initialized")
    
    def _define_tools(self) -> List[Dict]:
        """Define the function calling tools for Gemini"""
        return [
            {
                "name": "get_order_status",
                "description": "Recherche le statut d'une commande/colis par son numéro de suivi (tracking ID). Utilise cette fonction quand l'utilisateur demande 'où est mon colis', 'win rah', 'track', etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tracking_id": {
                            "type": "string",
                            "description": "Le numéro de suivi du colis (ex: TRK123456, BEX-ABC123, YAL-12345)"
                        }
                    },
                    "required": ["tracking_id"]
                }
            },
            {
                "name": "calculate_shipping_price",
                "description": "Calcule le prix de livraison vers une wilaya. Utilise cette fonction quand l'utilisateur demande 'chhal', 'combien', 'prix livraison', etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "wilaya": {
                            "type": "string",
                            "description": "Le nom de la wilaya de destination (ex: Alger, Oran, Constantine)"
                        },
                        "delivery_type": {
                            "type": "string",
                            "enum": ["domicile", "stopdesk"],
                            "description": "Type de livraison: 'domicile' (à la maison) ou 'stopdesk' (point relais)"
                        }
                    },
                    "required": ["wilaya"]
                }
            }
        ]
    
    async def connect(self):
        """Initialize MongoDB connection"""
        if not self.client:
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
    
    # ============================================
    # 🔧 TOOL IMPLEMENTATIONS
    # ============================================
    
    async def get_order_status(self, tracking_id: str) -> Dict[str, Any]:
        """
        Fetch order status from database
        
        Args:
            tracking_id: Order tracking ID (TRK, BEX-, YAL-, etc.)
            
        Returns:
            Order information dict or error
        """
        await self.connect()
        
        # Normalize tracking ID
        tracking_id_upper = tracking_id.upper().strip()
        
        # Try multiple search patterns
        order = None
        
        # Search by tracking_id
        order = await self.db.orders.find_one(
            {"tracking_id": {"$regex": tracking_id_upper, "$options": "i"}},
            {"_id": 0}
        )
        
        if not order:
            # Search by carrier_tracking_id
            order = await self.db.orders.find_one(
                {"carrier_tracking_id": {"$regex": tracking_id_upper, "$options": "i"}},
                {"_id": 0}
            )
        
        if not order:
            # Search by id
            order = await self.db.orders.find_one(
                {"id": tracking_id},
                {"_id": 0}
            )
        
        if not order:
            return {
                "found": False,
                "tracking_id": tracking_id,
                "message": f"Aucune commande trouvée avec le numéro {tracking_id}"
            }
        
        # Format status in French/Darja
        status_map = {
            "in_stock": "في المخزن (En stock)",
            "pending": "في الانتظار (En attente)",
            "preparing": "قيد التحضير (En préparation)",
            "ready_to_ship": "جاهز للشحن (Prêt à expédier)",
            "picked_up": "تم الاستلام (Récupéré)",
            "in_transit": "في الطريق 🚚 (En transit)",
            "out_for_delivery": "جاري التوصيل (En cours de livraison)",
            "delivered": "تم التوصيل ✅ (Livré)",
            "returned": "مرجع (Retourné)",
            "delivery_failed": "فشل التوصيل ❌ (Échec de livraison)",
            "cancelled": "ملغي (Annulé)"
        }
        
        status = order.get("status", "unknown")
        status_label = status_map.get(status, status)
        
        recipient = order.get("recipient", {})
        
        return {
            "found": True,
            "tracking_id": order.get("tracking_id", tracking_id),
            "status": status,
            "status_label": status_label,
            "destination": {
                "wilaya": recipient.get("wilaya", "N/A"),
                "commune": recipient.get("commune", ""),
                "address": recipient.get("address", "")
            },
            "recipient_name": recipient.get("name", "Client"),
            "cod_amount": order.get("cod_amount", 0),
            "carrier": order.get("carrier_type", "Beyond Express"),
            "carrier_tracking_id": order.get("carrier_tracking_id"),
            "description": order.get("description", ""),
            "created_at": order.get("created_at"),
            "last_update": order.get("updated_at")
        }
    
    def calculate_shipping_price(self, wilaya: str, delivery_type: str = "domicile") -> Dict[str, Any]:
        """
        Calculate shipping price for a wilaya
        
        Args:
            wilaya: Destination wilaya name
            delivery_type: 'domicile' or 'stopdesk'
            
        Returns:
            Pricing information
        """
        # Normalize wilaya name
        wilaya_lower = wilaya.lower().strip()
        
        # Remove common prefixes
        wilaya_lower = wilaya_lower.replace("wilaya de ", "").replace("wilaya d'", "")
        
        # Find in pricing grid
        pricing = ALGERIA_PRICING.get(wilaya_lower, DEFAULT_PRICING)
        
        # Get price based on delivery type
        delivery_type = delivery_type.lower() if delivery_type else "domicile"
        if delivery_type not in ["domicile", "stopdesk"]:
            delivery_type = "domicile"
        
        price = pricing.get(delivery_type, pricing.get("domicile"))
        
        return {
            "wilaya": wilaya.title(),
            "delivery_type": delivery_type,
            "price": price,
            "domicile_price": pricing.get("domicile"),
            "stopdesk_price": pricing.get("stopdesk"),
            "currency": "DA"
        }
    
    # ============================================
    # 🤖 MAIN CHAT METHOD
    # ============================================
    
    async def chat(self, user_message: str, api_key: str, session_id: str = None) -> Dict[str, Any]:
        """
        Main chat method - Process user message and generate response
        Uses emergentintegrations for Gemini with manual function handling
        
        Args:
            user_message: User's message
            api_key: Emergent LLM API key
            session_id: Optional session ID for context
            
        Returns:
            Response dict with message, provider, model
        """
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage as LlmUserMessage
            
            # Step 1: Check for tracking ID in message and get order info
            tracking_match = re.search(
                r'(TRK[\d]+|BEX-[\w]+|YAL-[\w]+|yal[\d]+)', 
                user_message, 
                re.IGNORECASE
            )
            
            context_addition = ""
            if tracking_match:
                tracking_id = tracking_match.group(1)
                logger.info(f"🔍 Found tracking ID: {tracking_id}")
                
                order_info = await self.get_order_status(tracking_id)
                
                if order_info.get("found"):
                    context_addition = f"""

📦 معلومات الطرد (INFO COMMANDE):
- رقم التتبع: {order_info['tracking_id']}
- الحالة: {order_info['status_label']}
- الوجهة: {order_info['destination']['wilaya']}, {order_info['destination']['commune']}
- المبلغ COD: {order_info['cod_amount']} دج
- الناقل: {order_info.get('carrier', 'Beyond Express')}
"""
                    if order_info.get('carrier_tracking_id'):
                        context_addition += f"- رقم الناقل: {order_info['carrier_tracking_id']}\n"
                else:
                    context_addition = f"\n❌ لم يتم العثور على طرد برقم: {tracking_id}\n"
            
            # Step 2: Check for price query
            price_match = re.search(
                r'(?:prix|chhal|combien|tarif|كم|سعر).*?(?:vers|pour|à|l[\'e]?|ل|إلى)\s*(\w+)', 
                user_message, 
                re.IGNORECASE
            )
            
            if price_match:
                wilaya = price_match.group(1)
                logger.info(f"💰 Price query for: {wilaya}")
                
                pricing = self.calculate_shipping_price(wilaya)
                context_addition += f"""

💰 تعريفة الشحن (TARIF LIVRAISON):
- الولاية: {pricing['wilaya']}
- التوصيل للمنزل (Domicile): {pricing['domicile_price']} دج
- نقطة الاستلام (Stop Desk): {pricing['stopdesk_price']} دج
"""
            
            # Step 3: Build full prompt
            full_system = AMINE_SYSTEM_PROMPT + context_addition
            
            # Step 4: Use emergentintegrations with Gemini
            chat = LlmChat(
                api_key=api_key,
                session_id=session_id or "amine-default",
                system_message=full_system
            ).with_model("gemini", "gemini-2.5-flash")
            
            # Send message
            llm_message = LlmUserMessage(text=user_message)
            response = await chat.send_message(llm_message)
            
            logger.info(f"✅ Amine responded successfully")
            
            return {
                "response": response,
                "provider": "Google Gemini",
                "model": "gemini-2.5-flash",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Amine chat error: {str(e)}")
            
            # Fallback: Try to give a helpful response based on extracted data
            fallback_response = await self._generate_fallback_response(user_message)
            if fallback_response:
                return fallback_response
            
            return {
                "response": f"Désolé, j'ai un problème technique. Ma tkezerch rassek, ça va s'arranger! 🙏\n\nErreur: {str(e)[:100]}",
                "provider": "Google Gemini",
                "model": "error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _generate_fallback_response(self, user_message: str) -> Optional[Dict[str, Any]]:
        """Generate a response without LLM if we have concrete data"""
        
        # Check for tracking ID
        tracking_match = re.search(r'(TRK[\d]+|BEX-[\w]+|YAL-[\w]+)', user_message, re.IGNORECASE)
        if tracking_match:
            tracking_id = tracking_match.group(1)
            order_info = await self.get_order_status(tracking_id)
            
            if order_info.get("found"):
                response = f"""مرحبا بيك! 👋

📦 طردك رقم **{order_info['tracking_id']}** موجود!

🚚 **الحالة**: {order_info['status_label']}
📍 **الوجهة**: {order_info['destination']['wilaya']}
💰 **المبلغ COD**: {order_info['cod_amount']} دج

إن شاء الله يوصلك قريب! 🤲"""
                
                return {
                    "response": response,
                    "provider": "Beyond Express",
                    "model": "fallback",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        
        # Check for price query
        price_match = re.search(r'(?:prix|chhal|combien|tarif).*?(\w+)', user_message, re.IGNORECASE)
        if price_match:
            wilaya = price_match.group(1)
            pricing = self.calculate_shipping_price(wilaya)
            
            response = f"""مرحبا بيك! 👋

💰 تعريفة الشحن إلى **{pricing['wilaya']}**:

🏠 **التوصيل للمنزل**: {pricing['domicile_price']} دج
📍 **Stop Desk**: {pricing['stopdesk_price']} دج

هل تحب نساعدك بشيء آخر؟ 😊"""
            
            return {
                "response": response,
                "provider": "Beyond Express",
                "model": "fallback",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        return None


# Singleton instance
amine_agent = AmineAgent()
