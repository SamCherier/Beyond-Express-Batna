"""
AI Assistant Routes with Usage Tracking
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from pydantic import BaseModel
import os
import logging

from models import User

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Get Emergent LLM Key
emergent_api_key = os.environ.get('EMERGENT_LLM_KEY', '')

# Auth dependency placeholder
async def get_current_user_dependency():
    """Placeholder - will be replaced by actual dependency from server.py"""
    raise HTTPException(status_code=500, detail="Auth dependency not configured")

class AIMessageRequest(BaseModel):
    message: str
    model: str = "gpt-4o"
    provider: str = "openai"  # openai, anthropic, gemini
    session_id: str

class AIMessageResponse(BaseModel):
    response: str
    usage_count: int
    limit: int
    remaining: int

@router.post("/message", response_model=AIMessageResponse)
async def send_ai_message(
    request: AIMessageRequest,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Send message to AI assistant with usage tracking
    
    Feature Locking:
    - FREE: No access (should be blocked on frontend)
    - STARTER: Limited access (0 uses - no AI generator in specs)
    - PRO: 200 uses per month
    - BUSINESS: Unlimited
    """
    try:
        user_id = current_user.id
        current_plan = current_user.current_plan or 'free'
        
        # Define limits per plan
        plan_limits = {
            'free': 0,  # No access
            'starter': 0,  # No AI generator in STARTER plan
            'pro': 200,  # 200 uses per month
            'business': -1  # Unlimited
        }
        
        limit = plan_limits.get(current_plan, 0)
        
        # Check if user has access
        if limit == 0:
            raise HTTPException(
                status_code=403, 
                detail=f"Plan {current_plan.upper()} doesn't have access to AI Assistant. Upgrade to PRO or BUSINESS."
            )
        
        # Get current usage for this month
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        usage_collection = db["ai_usage"]
        current_usage = await usage_collection.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": month_start}
        })
        
        # Check if limit reached (skip for unlimited)
        if limit != -1 and current_usage >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"AI usage limit reached ({limit} messages/month). Upgrade to BUSINESS for unlimited access."
            )
        
        # Call AI API using emergentintegrations
        ai_response = await call_ai_api(request.message, request.model, request.provider, request.session_id)
        
        # Record usage
        usage_record = {
            "user_id": user_id,
            "plan": current_plan,
            "message": request.message[:100],  # Store first 100 chars for reference
            "model": request.model,
            "provider": request.provider,
            "session_id": request.session_id,
            "response_length": len(ai_response),
            "created_at": now
        }
        await usage_collection.insert_one(usage_record)
        
        # Calculate remaining
        remaining = -1 if limit == -1 else (limit - current_usage - 1)
        
        logger.info(f"✅ AI message sent for user {user_id} (plan: {current_plan}, usage: {current_usage + 1}/{limit})")
        
        return AIMessageResponse(
            response=ai_response,
            usage_count=current_usage + 1,
            limit=limit,
            remaining=remaining
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Assistant error: {str(e)}")

async def call_ai_api(message: str, model: str, provider: str, session_id: str) -> str:
    """
    Call AI API using emergentintegrations
    Supports: OpenAI (GPT-4o, GPT-5), Anthropic (Claude), Gemini
    """
    try:
        from emergentintegrations import get_universal_client
        
        client = get_universal_client(provider=provider, api_key=emergent_api_key)
        
        messages = [
            {
                "role": "system",
                "content": """Vous êtes l'assistant IA de Beyond Express, une plateforme 3PL logistique en Algérie.
Vous aidez les utilisateurs avec:
- Suivi et gestion des commandes
- Questions sur les stocks
- Informations sur les livraisons
- Conseils logistiques
- Fonctionnalités de la plateforme

Répondez toujours en français, de manière claire, concise et professionnelle."""
            },
            {
                "role": "user",
                "content": message
            }
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"AI API error: {str(e)}")
        raise Exception(f"Failed to communicate with {provider} {model}: {str(e)}")

@router.get("/usage")
async def get_ai_usage(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Get current AI usage for the user
    """
    try:
        user_id = current_user.id
        current_plan = current_user.current_plan or 'free'
        
        # Define limits
        plan_limits = {
            'free': 0,
            'starter': 0,
            'pro': 200,
            'business': -1
        }
        
        limit = plan_limits.get(current_plan, 0)
        
        # Get current month usage
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        usage_collection = db["ai_usage"]
        current_usage = await usage_collection.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": month_start}
        })
        
        remaining = -1 if limit == -1 else max(0, limit - current_usage)
        
        return {
            "plan": current_plan,
            "limit": limit,
            "used": current_usage,
            "remaining": remaining,
            "has_access": limit != 0
        }
    
    except Exception as e:
        logger.error(f"Error getting AI usage: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get AI usage")
