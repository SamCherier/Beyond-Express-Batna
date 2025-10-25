"""
WhatsApp API Routes
Provides REST endpoints for WhatsApp messaging and conversation management
"""
from fastapi import APIRouter, HTTPException, Request, Form, Depends, BackgroundTasks
from fastapi.responses import Response
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
import os
import logging
from typing import Optional

from models import SendWhatsAppMessageRequest, User
from services.twilio_service import twilio_service
from services.webhook_service import webhook_service
# Import get_current_user from server (will be available at runtime)
import sys
sys.path.insert(0, '/app/backend')
from server import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== MESSAGE SENDING ENDPOINTS =====

@router.post("/send")
async def send_whatsapp_message(
    request: SendWhatsAppMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Send a WhatsApp message to a customer
    
    Requires authentication. Admin or Ecommerce users can send messages.
    """
    # Validate phone number format
    if not request.to_phone.startswith("+"):
        raise HTTPException(
            status_code=400,
            detail="Phone number must be in E.164 format (e.g., +213550123456)"
        )
    
    # Get webhook URL from environment
    webhook_base_url = os.environ.get('WEBHOOK_BASE_URL', '')
    status_callback_url = f"{webhook_base_url}/api/whatsapp/webhook/status" if webhook_base_url else None
    
    # Send message via Twilio
    result = twilio_service.send_whatsapp_message(
        to_phone=request.to_phone,
        message_body=request.message_body,
        status_callback_url=status_callback_url
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to send message")
        )
    
    # Store message in MongoDB asynchronously
    async def store_message():
        await webhook_service.connect()
        messages_collection = webhook_service.db["whatsapp_messages"]
        conversation_id = f"conv_{request.to_phone.replace('+', '')}"
        
        message_doc = {
            "id": result["message_sid"],
            "message_sid": result["message_sid"],
            "conversation_id": conversation_id,
            "sender_phone": result["from"].replace("whatsapp:", ""),
            "recipient_phone": request.to_phone,
            "body": request.message_body,
            "direction": "outbound",
            "status": result["status"],
            "timestamp": webhook_service.db.command("serverStatus")["localTime"],
            "created_at": webhook_service.db.command("serverStatus")["localTime"],
            "updated_at": webhook_service.db.command("serverStatus")["localTime"],
            "metadata": {"order_id": request.order_id} if request.order_id else {}
        }
        
        await messages_collection.insert_one(message_doc)
    
    background_tasks.add_task(store_message)
    
    return {
        "success": True,
        "message_sid": result["message_sid"],
        "status": result["status"],
        "to": request.to_phone
    }

@router.post("/send-order-confirmation/{order_id}")
async def send_order_confirmation_message(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Send an order confirmation message via WhatsApp
    
    Fetches order details from database and sends formatted confirmation message.
    """
    await webhook_service.connect()
    
    # Fetch order details
    orders_collection = webhook_service.db["orders"]
    order = await orders_collection.find_one({"id": order_id})
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get customer phone from order
    customer_phone = order.get("recipient", {}).get("phone")
    if not customer_phone:
        raise HTTPException(status_code=400, detail="Order has no customer phone number")
    
    # Send confirmation message
    result = twilio_service.send_order_confirmation(
        to_phone=customer_phone,
        order_id=order["id"],
        tracking_id=order.get("tracking_id", "N/A"),
        customer_name=order.get("recipient", {}).get("name", "Client"),
        items_description=order.get("description", "Produits"),
        cod_amount=order.get("cod_amount", 0)
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to send confirmation")
        )
    
    return {
        "success": True,
        "message_sid": result["message_sid"],
        "order_id": order_id,
        "customer_phone": customer_phone
    }

# ===== WEBHOOK ENDPOINTS =====

@router.post("/webhook/incoming")
async def handle_incoming_whatsapp_message(
    request: Request,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...)
):
    """
    Webhook endpoint to receive incoming WhatsApp messages from Twilio
    
    This endpoint is called by Twilio when a customer sends a message.
    It validates the Twilio signature, processes the message, and returns a TwiML response.
    """
    # Validate Twilio signature for security
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
    if auth_token:
        validator = RequestValidator(auth_token)
        twilio_signature = request.headers.get("X-Twilio-Signature", "")
        
        # Get full URL
        url = str(request.url)
        
        # Get form data
        form_data = await request.form()
        form_dict = dict(form_data)
        
        if not validator.validate(url, form_dict, twilio_signature):
            logger.warning(f"⚠️ Invalid Twilio signature received from {From}")
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        # Process the incoming message
        result = await webhook_service.process_incoming_message(
            sender_phone=From,
            recipient_phone=To,
            message_body=Body,
            message_sid=MessageSid
        )
        
        logger.info(f"✅ Processed incoming message: {result}")
        
        # Return TwiML response (empty for now - AI will respond later)
        response = MessagingResponse()
        # Don't auto-reply here - let AI agent handle it
        
        return Response(
            content=str(response),
            media_type="application/xml"
        )
    
    except Exception as e:
        logger.error(f"❌ Error processing incoming message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/webhook/status")
async def handle_message_status_callback(
    request: Request,
    MessageSid: str = Form(...),
    MessageStatus: str = Form(...)
):
    """
    Webhook endpoint to receive message delivery status updates from Twilio
    
    Called by Twilio when message status changes (queued → sent → delivered → read)
    """
    # Validate Twilio signature
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
    if auth_token:
        validator = RequestValidator(auth_token)
        twilio_signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        form_data = await request.form()
        form_dict = dict(form_data)
        
        if not validator.validate(url, form_dict, twilio_signature):
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        # Update message status in database
        await webhook_service.update_message_status(
            message_sid=MessageSid,
            status=MessageStatus
        )
        
        return {"status": "ok", "message_sid": MessageSid}
    
    except Exception as e:
        logger.error(f"❌ Error updating message status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ===== CONVERSATION MANAGEMENT ENDPOINTS =====

@router.get("/conversations")
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List all WhatsApp conversations
    
    Supports filtering by status (ai_handling, human_handling, closed)
    """
    await webhook_service.connect()
    
    conversations_collection = webhook_service.db["whatsapp_conversations"]
    
    # Build query
    query = {"is_active": True}
    if status:
        query["status"] = status
    
    try:
        cursor = conversations_collection.find(query).sort("last_message_at", -1).skip(skip).limit(limit)
        
        conversations = []
        async for conv in cursor:
            conv["_id"] = str(conv["_id"])
            conv["created_at"] = conv["created_at"].isoformat()
            conv["updated_at"] = conv["updated_at"].isoformat()
            conv["last_message_at"] = conv["last_message_at"].isoformat()
            conversations.append(conv)
        
        return {
            "total": len(conversations),
            "conversations": conversations
        }
    
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list conversations")

@router.get("/conversation/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Get all messages for a specific conversation
    """
    messages = await webhook_service.get_conversation_messages(
        conversation_id=conversation_id,
        limit=limit
    )
    
    return {
        "conversation_id": conversation_id,
        "message_count": len(messages),
        "messages": messages
    }

@router.post("/conversation/{conversation_id}/assign")
async def assign_conversation_to_human(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Transfer conversation from AI to human agent
    """
    await webhook_service.connect()
    
    conversations_collection = webhook_service.db["whatsapp_conversations"]
    
    try:
        result = await conversations_collection.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "status": "human_handling",
                    "assigned_agent": current_user.id,
                    "updated_at": webhook_service.db.command("serverStatus")["localTime"]
                }
            }
        )
        
        if result.modified_count > 0:
            return {
                "success": True,
                "conversation_id": conversation_id,
                "assigned_to": current_user.name
            }
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    
    except Exception as e:
        logger.error(f"Error assigning conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to assign conversation")

@router.post("/conversation/{conversation_id}/mark-read")
async def mark_conversation_read(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Mark conversation as read (reset unread count)
    """
    success = await webhook_service.mark_conversation_read(conversation_id)
    
    if success:
        return {"success": True, "conversation_id": conversation_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to mark as read")
