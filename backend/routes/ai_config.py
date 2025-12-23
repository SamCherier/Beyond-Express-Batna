from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from models import User
import logging
import google.generativeai as genai
import sys
sys.path.append('/app/backend')
from server import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

class AIConfig(BaseModel):
    provider: str  # 'gemini', 'deepseek', 'openai'
    api_key: str
    model_name: Optional[str] = None

class TestAIRequest(BaseModel):
    message: str = "Bonjour"

@router.post("/config")
async def save_ai_config(config: AIConfig, current_user: User = Depends(get_current_user)):
    """Save AI configuration for user"""
    try:
        from server import db
        
        # Validate provider
        valid_providers = ['gemini', 'deepseek', 'openai']
        if config.provider not in valid_providers:
            raise HTTPException(status_code=400, detail="Invalid provider")
        
        # Save to database
        await db.ai_configs.update_one(
            {"user_id": current_user.id},
            {
                "$set": {
                    "provider": config.provider,
                    "api_key": config.api_key,  # In production, encrypt this!
                    "model_name": config.model_name or "gemini-1.5-flash",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Configuration IA sauvegardée avec succès"
        }
        
    except Exception as e:
        logger.error(f"Error saving AI config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_ai_config(current_user: User = Depends(get_current_user)):
    """Get AI configuration for user"""
    try:
        from server import db
        
        config = await db.ai_configs.find_one(
            {"user_id": current_user.id},
            {"_id": 0}
        )
        
        if config:
            # Mask API key (show only last 4 chars)
            api_key = config.get('api_key', '')
            if len(api_key) > 4:
                config['api_key_masked'] = '*' * (len(api_key) - 4) + api_key[-4:]
            else:
                config['api_key_masked'] = '****'
            
            # Remove full API key from response
            config.pop('api_key', None)
            
            return config
        
        # Return default config
        return {
            "provider": "gemini",
            "model_name": "gemini-1.5-flash",
            "api_key_masked": "****"
        }
        
    except Exception as e:
        logger.error(f"Error fetching AI config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def test_ai_connection(test_request: TestAIRequest, current_user: User = Depends(get_current_user)):
    """Test AI connection with saved config"""
    try:
        from server import db
        
        # Get user's AI config
        config = await db.ai_configs.find_one({"user_id": current_user.id})
        
        if not config:
            raise HTTPException(
                status_code=404, 
                detail="Configuration IA non trouvée. Veuillez configurer votre clé API d'abord."
            )
        
        provider = config.get('provider')
        api_key = config.get('api_key')
        
        if provider == 'gemini':
            # Test Gemini
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            response = model.generate_content(test_request.message)
            
            return {
                "success": True,
                "provider": "Google Gemini",
                "model": "gemini-1.5-flash",
                "response": response.text,
                "message": "Connexion réussie !"
            }
        
        elif provider == 'deepseek':
            # TODO: Implement DeepSeek
            return {
                "success": True,
                "provider": "DeepSeek V3",
                "message": "DeepSeek API à implémenter"
            }
        
        elif provider == 'openai':
            # TODO: Implement OpenAI
            return {
                "success": True,
                "provider": "OpenAI",
                "message": "OpenAI API à implémenter"
            }
        
        else:
            raise HTTPException(status_code=400, detail="Provider non supporté")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing AI: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Erreur de connexion. Vérifiez votre clé API."
        }
