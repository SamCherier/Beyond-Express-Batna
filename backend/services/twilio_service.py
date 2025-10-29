"""
Twilio WhatsApp Service
Handles sending WhatsApp messages via Twilio API
"""
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TwilioService:
    """Service for interacting with Twilio WhatsApp API"""
    
    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        
        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials not configured. WhatsApp functionality will not work.")
            self.client = None
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
                self.client = None
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to WhatsApp format"""
        if phone.startswith("whatsapp:"):
            return phone
        
        # Remove all spaces, dashes, and parentheses
        phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Handle Algerian numbers specifically
        if phone.startswith("0"):
            # Algerian local format (0550096136) → +213550096136
            phone = "+213" + phone[1:]
        elif phone.startswith("+0"):
            # Fix incorrect format (+0550096136) → +213550096136
            phone = "+213" + phone[2:]
        elif not phone.startswith("+"):
            # No country code, assume Algeria
            phone = f"+213{phone}"
        
        return f"whatsapp:{phone}"
    
    def send_whatsapp_message(
        self,
        to_phone: str,
        message_body: str,
        status_callback_url: Optional[str] = None
    ) -> Dict:
        """
        Send a WhatsApp message using Twilio API
        
        Args:
            to_phone: Recipient phone number in E.164 format
            message_body: Text content of the message
            status_callback_url: URL for delivery status callbacks
            
        Returns:
            Dict with success status, message_sid, and status
        """
        if not self.client:
            logger.error("Twilio client not initialized. Cannot send message.")
            return {
                "success": False,
                "error": "Twilio not configured. Please add TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN to .env"
            }
        
        # Normalize phone numbers
        to_phone = self._normalize_phone(to_phone)
        from_number = self.whatsapp_number
        
        try:
            message = self.client.messages.create(
                from_=from_number,
                to=to_phone,
                body=message_body,
                status_callback=status_callback_url
            )
            
            logger.info(f"✅ WhatsApp message sent: {message.sid} to {to_phone}")
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": to_phone,
                "from": from_number
            }
        
        except TwilioRestException as e:
            logger.error(f"❌ Twilio API error: {e.code} - {e.msg}")
            return {
                "success": False,
                "error": f"Twilio error {e.code}: {e.msg}",
                "error_code": e.code
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp message: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_order_confirmation(
        self,
        to_phone: str,
        order_id: str,
        tracking_id: str,
        customer_name: str,
        items_description: str,
        cod_amount: float
    ) -> Dict:
        """
        Send an order confirmation message via WhatsApp
        
        Args:
            to_phone: Customer phone number
            order_id: Order ID
            tracking_id: Tracking number
            customer_name: Customer name
            items_description: Description of items
            cod_amount: Cash on delivery amount
            
        Returns:
            Dict with success status and message details
        """
        message_body = f"""🎉 *Confirmation de Commande - Beyond Express*

Bonjour {customer_name},

Nous avons bien reçu votre commande !

📦 *Détails de la Commande:*
• N° Commande: {order_id}
• N° Suivi: {tracking_id}
• Produits: {items_description}
• Montant: {cod_amount:,.0f} DA

Pour confirmer votre commande, répondez:
✅ "CONFIRMER" pour valider
❌ "ANNULER" pour annuler

Merci de votre confiance ! 🚀"""
        
        return self.send_whatsapp_message(
            to_phone=to_phone,
            message_body=message_body,
            status_callback_url=f"{os.environ.get('WEBHOOK_BASE_URL', '')}/api/whatsapp/webhook/status"
        )
    
    def get_message_status(self, message_sid: str) -> Dict:
        """
        Retrieve the current status of a sent message
        
        Args:
            message_sid: Twilio message SID
            
        Returns:
            Dict with message status information
        """
        if not self.client:
            return {"error": "Twilio not configured"}
        
        try:
            message = self.client.messages.get(message_sid).fetch()
            return {
                "message_sid": message_sid,
                "status": message.status,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                "date_updated": message.date_updated.isoformat() if message.date_updated else None
            }
        except TwilioRestException as e:
            logger.error(f"Error fetching message status: {e.msg}")
            return {"error": str(e.msg)}
        except Exception as e:
            logger.error(f"Error fetching message status: {str(e)}")
            return {"error": str(e)}

# Singleton instance
twilio_service = TwilioService()
