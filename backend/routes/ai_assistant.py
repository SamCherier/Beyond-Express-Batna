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
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Get Emergent LLM Key
emergent_api_key = os.environ.get('EMERGENT_LLM_KEY', '')

# Auth dependency - copied from server.py to avoid circular imports
from fastapi import Request, Cookie
from typing import Optional
from auth_utils import verify_token
import uuid

async def get_current_user(request: Request, session_token: Optional[str] = Cookie(None)) -> User:
    """Auth dependency for AI assistant routes"""
    token = session_token
    
    # Fallback to Authorization header if cookie not present
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Try session token first
    session_doc = await db.sessions.find_one({"session_token": token}, {"_id": 0})
    if session_doc:
        from datetime import datetime, timezone
        if datetime.fromisoformat(session_doc['expires_at']) > datetime.now(timezone.utc):
            user_doc = await db.users.find_one({"id": session_doc['user_id']}, {"_id": 0})
            if user_doc:
                return User(**user_doc)
    
    # Try JWT token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)

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
    current_user: User = Depends(get_current_user)
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
        # Convert Enum to string if needed
        current_plan = current_user.current_plan
        if hasattr(current_plan, 'value'):
            current_plan = current_plan.value
        else:
            current_plan = str(current_plan).lower() if current_plan else 'free'
        
        # Fallback for legacy plans (business → pro)
        plan_migration_map = {
            'business': 'pro',
            'basic': 'beginner'
        }
        if current_plan in plan_migration_map:
            logger.info(f"🔄 Migrating legacy plan '{current_plan}' → '{plan_migration_map[current_plan]}'")
            current_plan = plan_migration_map[current_plan]
        
        # Define limits per plan (NEW official plans)
        plan_limits = {
            'free': 0,        # No AI access during trial
            'beginner': 0,    # No AI for beginners
            'starter': 500,   # BEYOND STARTER: 500 messages/month
            'pro': 1000       # BEYOND PRO: 1000 messages/month
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
    
    For Gemini: Uses Amine Agent 🇩🇿 (The Algerian AI)
    """
    try:
        # 🇩🇿 For Gemini, use Amine Agent with function calling
        if provider == "gemini":
            from services.amine_agent import amine_agent
            
            # Amine needs a Gemini API key - use Emergent key
            result = await amine_agent.chat(
                user_message=message,
                api_key=emergent_api_key,
                session_id=session_id
            )
            return result.get("response", "Désolé, je n'ai pas pu traiter votre demande.")
        
        # For other providers, use emergentintegrations
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Set system message (Algerian style for all)
        system_message = """أنت "أمين" (Amine)، مساعد Beyond Express. أنت جزائري 🇩🇿 وتتكلم بالدارجة الجزائرية والفرنسية والعربية.

شخصيتك:
- ودود ومحترف
- تستعمل التعبيرات الجزائرية: "مرحبا بيك!", "ما تخمش راسك", "كاين مشكل؟ نحلولك!"
- تساعد في: تتبع الطرود، حساب الأسعار، إدارة الطلبات

معلومات Beyond Express:
- شركة لوجستيك جزائرية متخصصة في توصيل الطرود
- خدمة الدفع عند الاستلام (COD)
- تغطية كل 58 ولاية جزائرية
- إشعارات واتساب أوتوماتيكية

التعريفة:
- الجزائر العاصمة: 400 دج
- وهران: 550 دج
- قسنطينة: 600 دج
- باقي الولايات: 500-800 دج"""
        
        # Use LlmChat with system message
        chat = LlmChat(
            api_key=emergent_api_key,
            session_id=session_id,
            system_message=system_message
        ).with_model(provider, model)
        
        # Send user message
        user_message = UserMessage(text=message)
        response = await chat.send_message(user_message)
        
        return response
    
    except Exception as e:
        logger.error(f"AI API error: {str(e)}")
        raise Exception(f"Failed to communicate with {provider} {model}: {str(e)}")

@router.get("/usage")
async def get_ai_usage(
    current_user: User = Depends(get_current_user)
):
    """
    Get current AI usage for the user
    """
    try:
        user_id = current_user.id
        # Convert Enum to string if needed
        current_plan = current_user.current_plan
        if hasattr(current_plan, 'value'):
            current_plan = current_plan.value
        else:
            current_plan = str(current_plan).lower() if current_plan else 'free'
        
        # Fallback for legacy plans (business → pro)
        plan_migration_map = {
            'business': 'pro',
            'basic': 'beginner'
        }
        if current_plan in plan_migration_map:
            logger.info(f"🔄 Migrating legacy plan '{current_plan}' → '{plan_migration_map[current_plan]}'")
            current_plan = plan_migration_map[current_plan]
        
        # DEBUG LOGS
        logger.info(f"🔍 AI Usage Check - User: {user_id}, Plan: {current_plan}, Type: {type(current_plan)}")
        
        # Define limits based on NEW official plans
        plan_limits = {
            'free': 0,        # No AI access
            'beginner': 0,    # No AI access
            'starter': 500,   # BEYOND STARTER: 500 messages/month
            'pro': 1000       # BEYOND PRO: 1000 messages/month (UNLIMITED = -1 if needed)
        }
        
        limit = plan_limits.get(current_plan, 0)
        logger.info(f"🔍 Limit retrieved: {limit} for plan '{current_plan}'")
        logger.info(f"🔍 Plan limits dict keys: {list(plan_limits.keys())}")
        
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
