from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from models import User
import logging
import google.generativeai as genai
import sys
sys.path.append('/app/backend')
from server import get_current_user
from services.amine_agent import amine_agent

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    tracking_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    timestamp: str

BEYOND_EXPRESS_CONTEXT = """
Tu es l'assistant intelligent de la plateforme logistique algérienne 'Beyond Express'.

TES RÈGLES D'OR :
1. LANGUE : Si l'utilisateur parle en Darja/Arabe, RÉPONDS EN DARJA ALGÉRIENNE (Ex: 'Marhba bik', 'Kayen stock', 'Chouf m3a le fournisseur'). Si Français -> Français.
2. RÔLE : Tu es un expert logistique. Tu aides à tracker les colis, calculer les tarifs (400DA Alger, 500DA Oran, autres wilayas variable) et gérer le stock.
3. PERSONNALITÉ : Professionnel mais chaleureux, comme un partenaire algérien de confiance.

FONCTIONNALITÉS DE BEYOND EXPRESS :
- Suivi de colis en temps réel
- Gestion financière COD automatisée
- Notifications WhatsApp automatiques
- Import en masse de commandes
- Impression d'étiquettes thermiques
- API complète pour intégrations

TARIFS STANDARD :
- Alger : 400 DA
- Oran : 500 DA
- Autres wilayas : Variable selon destination

Utilise des emojis quand approprié : 📦 🚚 ✅ 💰
"""

@router.post("/send", response_model=ChatResponse)
async def send_chat_message(chat: ChatMessage, current_user: User = Depends(get_current_user)):
    """Send message to AI and get response"""
    try:
        from server import db
        
        # Get user's AI config
        config = await db.ai_configs.find_one({"user_id": current_user.id})
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail="Configuration IA non trouvée. Configurez votre clé API dans Paramètres > Configuration IA"
            )
        
        provider = config.get('provider')
        api_key = config.get('api_key')
        model_name = config.get('model_name', 'gemini-1.5-flash')
        
        # RAG: Get order info if tracking_id provided
        context_addition = ""
        if chat.tracking_id:
            order = await db.orders.find_one(
                {"tracking_id": chat.tracking_id},
                {"_id": 0}
            )
            if order:
                context_addition = f"\n\nInformation sur la commande {chat.tracking_id}:\n"
                context_addition += f"- Statut: {order.get('status')}\n"
                context_addition += f"- Destination: {order.get('recipient', {}).get('wilaya')}\n"
                context_addition += f"- Type de livraison: {order.get('delivery_type')}\n"
                if order.get('delivery_partner'):
                    context_addition += f"- Transporteur: {order.get('delivery_partner')}\n"
        
        # Generate response based on provider
        if provider == 'gemini':
            # 🇩🇿 Use Amine Agent - The Algerian AI
            result = await amine_agent.chat(
                user_message=chat.message,
                api_key=api_key,
                session_id=current_user.id
            )
            
            # Save to chat history
            await db.chat_history.insert_one({
                "user_id": current_user.id,
                "message": chat.message,
                "response": result["response"],
                "provider": provider,
                "model": result["model"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return ChatResponse(
                response=result["response"],
                provider=result["provider"],
                model=result["model"],
                timestamp=result["timestamp"]
            )
        
        elif provider == 'deepseek':
            # TODO: Implement DeepSeek API
            raise HTTPException(status_code=501, detail="DeepSeek API non encore implémenté")
        
        elif provider == 'openai':
            # TODO: Implement OpenAI API
            raise HTTPException(status_code=501, detail="OpenAI API non encore implémenté")
        
        else:
            raise HTTPException(status_code=400, detail="Provider non supporté")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_chat_history(limit: int = 20, current_user: User = Depends(get_current_user)):
    """Get chat history for user"""
    try:
        from server import db
        
        history = await db.chat_history.find(
            {"user_id": current_user.id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {"history": history, "count": len(history)}
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
