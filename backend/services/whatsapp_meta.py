"""WhatsApp Meta Cloud API Service — Zero Cost Direct Integration
Endpoint: https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages
Auth: Bearer {WHATSAPP_ACCESS_TOKEN}
"""
import os
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v17.0"

# Pre-defined templates matching Meta's approved template format
DEFAULT_TEMPLATES = {
    "hello_world": {
        "name": "hello_world",
        "language": "en_US",
        "category": "UTILITY",
        "label": "Hello World (Test)",
        "description": "Template de test Meta par défaut",
    },
    "delivery_update": {
        "name": "delivery_update",
        "language": "fr",
        "category": "UTILITY",
        "label": "En cours de livraison",
        "description": "Notification quand le colis est en route",
        "body": "Votre colis {{1}} est en cours de livraison. Livreur: {{2}}. Suivi: {{3}}",
    },
    "delivery_confirmed": {
        "name": "delivery_confirmed",
        "language": "fr",
        "category": "UTILITY",
        "label": "Livraison confirmée",
        "description": "Notification quand le colis est livré",
        "body": "Votre colis {{1}} a été livré avec succès. Merci pour votre confiance!",
    },
}

# Status triggers
STATUS_TRIGGERS = {
    "OUT_FOR_DELIVERY": "delivery_update",
    "DELIVERED": "delivery_confirmed",
}


class WhatsAppMetaService:
    """Direct Meta WhatsApp Cloud API — no third-party SDK."""

    def __init__(self):
        self._phone_id: Optional[str] = None
        self._access_token: Optional[str] = None
        self._enabled: bool = False
        self._triggers: dict = dict(STATUS_TRIGGERS)
        self._load_env()

    def _load_env(self):
        self._phone_id = os.environ.get("WHATSAPP_PHONE_ID")
        self._access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN")
        if self._phone_id and self._access_token:
            self._enabled = True
            logger.info("WhatsApp Meta service configured from env")

    @property
    def is_configured(self) -> bool:
        return bool(self._phone_id and self._access_token)

    def configure(self, phone_id: str, access_token: str, enabled: bool = True, triggers: dict = None):
        self._phone_id = phone_id
        self._access_token = access_token
        self._enabled = enabled
        if triggers:
            self._triggers = triggers

    def get_status(self) -> dict:
        return {
            "configured": self.is_configured,
            "enabled": self._enabled,
            "phone_id_set": bool(self._phone_id),
            "token_set": bool(self._access_token),
            "triggers": self._triggers,
            "templates": list(DEFAULT_TEMPLATES.values()),
        }

    async def send_template(self, to_phone: str, template_name: str, components: list = None) -> dict:
        """Send a template message via Meta Graph API."""
        if not self.is_configured:
            return {"success": False, "error": "WhatsApp non configuré. Ajoutez PHONE_ID et TOKEN."}

        to_phone = self._normalize_phone(to_phone)
        url = f"{GRAPH_API_BASE}/{self._phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        tpl_info = DEFAULT_TEMPLATES.get(template_name, {})
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": tpl_info.get("language", "en_US")},
            },
        }
        if components:
            payload["template"]["components"] = components

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=payload, headers=headers)
            data = resp.json()
            if resp.status_code in (200, 201):
                msg_id = data.get("messages", [{}])[0].get("id", "unknown")
                logger.info(f"WhatsApp sent to {to_phone} | msg_id={msg_id}")
                return {"success": True, "message_id": msg_id, "to": to_phone}
            else:
                err = data.get("error", {}).get("message", str(data))
                logger.error(f"Meta API error: {err}")
                return {"success": False, "error": err}
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_text(self, to_phone: str, text: str) -> dict:
        """Send a free-form text message."""
        if not self.is_configured:
            return {"success": False, "error": "WhatsApp non configuré."}

        to_phone = self._normalize_phone(to_phone)
        url = f"{GRAPH_API_BASE}/{self._phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": text},
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=payload, headers=headers)
            data = resp.json()
            if resp.status_code in (200, 201):
                msg_id = data.get("messages", [{}])[0].get("id", "unknown")
                return {"success": True, "message_id": msg_id, "to": to_phone}
            else:
                err = data.get("error", {}).get("message", str(data))
                return {"success": False, "error": err}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def on_order_status_change(self, order: dict, new_status: str, db=None):
        """Trigger WhatsApp notification on order status change."""
        if not self._enabled or not self.is_configured:
            return None

        template_name = self._triggers.get(new_status)
        if not template_name:
            return None

        phone = order.get("recipient", {}).get("phone", "")
        if not phone:
            return None

        tracking_id = order.get("tracking_id", "N/A")

        components = []
        if template_name == "delivery_update":
            driver = order.get("driver", {}).get("name", "Livreur")
            components = [{
                "type": "body",
                "parameters": [
                    {"type": "text", "text": tracking_id},
                    {"type": "text", "text": driver},
                    {"type": "text", "text": tracking_id},
                ],
            }]
        elif template_name == "delivery_confirmed":
            components = [{
                "type": "body",
                "parameters": [
                    {"type": "text", "text": tracking_id},
                ],
            }]

        result = await self.send_template(phone, template_name, components)

        if db and result.get("success"):
            await db.whatsapp_logs.insert_one({
                "type": "auto_trigger",
                "template": template_name,
                "to_phone": phone,
                "order_tracking": tracking_id,
                "status_trigger": new_status,
                "message_id": result.get("message_id"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        return result

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if phone.startswith("0"):
            phone = "213" + phone[1:]
        elif phone.startswith("+"):
            phone = phone[1:]
        return phone


whatsapp_meta = WhatsAppMetaService()
