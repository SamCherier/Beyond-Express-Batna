from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class NotificationTemplate(BaseModel):
    type: str  # order_confirmed, out_for_delivery, delivery_failed
    message: str
    enabled: bool = True

class SendNotificationRequest(BaseModel):
    order_id: str
    recipient_phone: str
    recipient_name: str
    template_type: str
    variables: dict  # Dynamic variables like {name}, {product}, {price}, etc.

class NotificationTemplateUpdate(BaseModel):
    templates: List[NotificationTemplate]

@router.post("/send")
async def send_notification(request: SendNotificationRequest, current_user: User):
    """
    Simulate sending a WhatsApp notification
    For MVP, this just logs the notification without actual WhatsApp API call
    """
    try:
        from server import db
        
        # Create notification log entry
        notification_log = {
            "id": f"notif_{datetime.now(timezone.utc).timestamp()}",
            "order_id": request.order_id,
            "recipient_phone": request.recipient_phone,
            "recipient_name": request.recipient_name,
            "template_type": request.template_type,
            "message": request.variables.get("message", ""),
            "status": "sent",  # For MVP, always "sent"
            "user_id": current_user.id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "delivery_status": "simulated"  # Indicates this is not real WhatsApp
        }
        
        await db.notification_logs.insert_one(notification_log)
        
        logger.info(f"Notification simulated for order {request.order_id}")
        
        return {
            "success": True,
            "message": "Notification envoyée avec succès",
            "notification_id": notification_log["id"],
            "simulated": True  # Indicates this is MVP simulation
        }
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_notification_templates(current_user: User):
    """Get user's notification templates"""
    try:
        from server import db
        
        # Get templates from user's settings or return defaults
        user_settings = await db.notification_settings.find_one(
            {"user_id": current_user.id},
            {"_id": 0}
        )
        
        if user_settings and "templates" in user_settings:
            return {"templates": user_settings["templates"]}
        
        # Default templates
        default_templates = [
            {
                "type": "order_confirmed",
                "name": "Confirmation de Commande",
                "message": "Bonjour {name}, votre commande de {product} à {price} DA est confirmée. Numéro de suivi: {tracking_id}",
                "enabled": True
            },
            {
                "type": "out_for_delivery",
                "name": "En Livraison",
                "message": "🚚 Le chauffeur arrive ! Préparez {total_cod} DA pour votre commande {tracking_id}",
                "enabled": True
            },
            {
                "type": "delivery_failed",
                "name": "Tentative Échouée",
                "message": "Nous n'avons pas pu vous livrer votre commande {tracking_id}. Contactez-nous pour reprogrammer.",
                "enabled": True
            },
            {
                "type": "delivered",
                "name": "Livraison Réussie",
                "message": "✅ Votre commande {tracking_id} a été livrée avec succès ! Merci de votre confiance. Beyond Express",
                "enabled": True
            }
        ]
        
        return {"templates": default_templates}
        
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/templates")
async def update_notification_templates(
    update: NotificationTemplateUpdate,
    current_user: User
):
    """Update user's notification templates"""
    try:
        from server import db
        
        templates_data = [t.dict() for t in update.templates]
        
        await db.notification_settings.update_one(
            {"user_id": current_user.id},
            {
                "$set": {
                    "templates": templates_data,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Templates mis à jour avec succès"
        }
        
    except Exception as e:
        logger.error(f"Error updating templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_notification_history(
    order_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = None
):
    """Get notification history for user or specific order"""
    try:
        from server import db
        
        query = {"user_id": current_user.id}
        if order_id:
            query["order_id"] = order_id
        
        notifications = await db.notification_logs.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {"notifications": notifications, "count": len(notifications)}
        
    except Exception as e:
        logger.error(f"Error fetching notification history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_notification_stats(current_user: User):
    """Get notification statistics for user"""
    try:
        from server import db
        
        total = await db.notification_logs.count_documents({"user_id": current_user.id})
        sent = await db.notification_logs.count_documents({
            "user_id": current_user.id,
            "status": "sent"
        })
        
        # Group by template type
        pipeline = [
            {"$match": {"user_id": current_user.id}},
            {"$group": {
                "_id": "$template_type",
                "count": {"$sum": 1}
            }}
        ]
        
        by_type = {}
        async for doc in db.notification_logs.aggregate(pipeline):
            by_type[doc["_id"]] = doc["count"]
        
        return {
            "total": total,
            "sent": sent,
            "by_type": by_type
        }
        
    except Exception as e:
        logger.error(f"Error fetching notification stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
