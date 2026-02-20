"""
WhatsApp Business Integration Service
WhatsApp messaging for customer communication
"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json
import hmac
import hashlib
import requests
import os

from app.core.config import settings


class WhatsAppService:
    """Service for WhatsApp Business API integration"""
    
    # WhatsApp Business API configuration
    API_VERSION = "v18.0"
    BASE_URL = "https://graph.facebook.com"
    
    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.webhook_verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
        self.app_secret = os.getenv('WHATSAPP_APP_SECRET')
    
    def _get_api_url(self, endpoint: str) -> str:
        """Get full API URL"""
        return f"{self.BASE_URL}/{self.API_VERSION}/{self.phone_number_id}/{endpoint}"
    
    def _get_headers(self) -> Dict:
        """Get API headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def send_text_message(
        self,
        to: str,
        message: str,
        preview_url: bool = False
    ) -> Dict:
        """Send a text message via WhatsApp"""
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": message
            }
        }
        
        try:
            response = requests.post(
                self._get_api_url("messages"),
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("messages", [{}])[0].get("id"),
                    "status": "sent"
                }
            else:
                return {
                    "success": False,
                    "error": response.json().get("error", {}).get("message", "Unknown error")
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: List[Dict] = None
    ) -> Dict:
        """Send a template message via WhatsApp"""
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            response = requests.post(
                self._get_api_url("messages"),
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("messages", [{}])[0].get("id"),
                    "status": "sent"
                }
            else:
                return {
                    "success": False,
                    "error": response.json().get("error", {}).get("message", "Unknown error")
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_interactive_message(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict],
        header: Dict = None,
        footer: str = None
    ) -> Dict:
        """Send an interactive message with buttons"""
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": body_text
                },
                "action": {
                    "buttons": buttons
                }
            }
        }
        
        if header:
            payload["interactive"]["header"] = header
        
        if footer:
            payload["interactive"]["footer"] = {"text": footer}
        
        try:
            response = requests.post(
                self._get_api_url("messages"),
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("messages", [{}])[0].get("id"),
                    "status": "sent"
                }
            else:
                return {
                    "success": False,
                    "error": response.json().get("error", {}).get("message", "Unknown error")
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_list_message(
        self,
        to: str,
        body_text: str,
        button_text: str,
        sections: List[Dict],
        header: str = None,
        footer: str = None
    ) -> Dict:
        """Send a list message for menu selection"""
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {
                    "text": body_text
                },
                "action": {
                    "button": button_text,
                    "sections": sections
                }
            }
        }
        
        if header:
            payload["interactive"]["header"] = {"type": "text", "text": header}
        
        if footer:
            payload["interactive"]["footer"] = {"text": footer}
        
        try:
            response = requests.post(
                self._get_api_url("messages"),
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("messages", [{}])[0].get("id"),
                    "status": "sent"
                }
            else:
                return {
                    "success": False,
                    "error": response.json().get("error", {}).get("message", "Unknown error")
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Dict:
        """Verify webhook subscription"""
        
        if mode == "subscribe" and token == self.webhook_verify_token:
            return {
                "verified": True,
                "challenge": challenge
            }
        
        return {"verified": False}
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature for security"""
        
        if not self.app_secret:
            return True  # Skip verification if no secret configured
        
        expected_signature = hmac.new(
            self.app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    def parse_webhook_payload(self, payload: Dict) -> Dict:
        """Parse incoming webhook payload"""
        
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            if "messages" in value:
                message = value["messages"][0]
                
                return {
                    "type": "message",
                    "from": message.get("from"),
                    "id": message.get("id"),
                    "timestamp": message.get("timestamp"),
                    "message_type": message.get("type"),
                    "text": message.get("text", {}).get("body") if message.get("type") == "text" else None,
                    "interactive": message.get("interactive") if message.get("type") == "interactive" else None,
                    "contacts": value.get("contacts", [])
                }
            
            elif "statuses" in value:
                status = value["statuses"][0]
                
                return {
                    "type": "status",
                    "id": status.get("id"),
                    "status": status.get("status"),
                    "timestamp": status.get("timestamp"),
                    "recipient_id": status.get("recipient_id")
                }
            
            return {"type": "unknown"}
            
        except Exception as e:
            return {"type": "error", "error": str(e)}
    
    async def mark_message_read(self, message_id: str) -> Dict:
        """Mark a message as read"""
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = requests.post(
                self._get_api_url("messages"),
                headers=self._get_headers(),
                json=payload
            )
            
            return {"success": response.status_code == 200}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_appointment_reminder(
        self,
        to: str,
        customer_name: str,
        appointment_time: str,
        service: str,
        business_name: str
    ) -> Dict:
        """Send appointment reminder via WhatsApp"""
        
        message = (
            f"📅 *Appointment Reminder*\n\n"
            f"Hi {customer_name}!\n\n"
            f"This is a reminder about your appointment:\n"
            f"🕐 *When:* {appointment_time}\n"
            f"📋 *Service:* {service}\n\n"
            f"Please reply with 'C' to confirm or 'R' to reschedule.\n\n"
            f"- {business_name}"
        )
        
        return await self.send_text_message(to, message)
    
    async def send_order_confirmation(
        self,
        to: str,
        customer_name: str,
        order_id: str,
        items: List[str],
        total: str,
        pickup_time: str = None,
        business_name: str = None
    ) -> Dict:
        """Send order confirmation via WhatsApp"""
        
        items_text = "\n".join([f"• {item}" for item in items])
        
        message = (
            f"✅ *Order Confirmed*\n\n"
            f"Hi {customer_name}!\n\n"
            f"Your order #{order_id} has been confirmed:\n"
            f"{items_text}\n\n"
            f"💰 *Total:* {total}\n"
        )
        
        if pickup_time:
            message += f"⏰ *Pickup:* {pickup_time}\n"
        
        if business_name:
            message += f"\n- {business_name}"
        
        return await self.send_text_message(to, message)
    
    async def send_menu_options(
        self,
        to: str,
        business_name: str
    ) -> Dict:
        """Send interactive menu options"""
        
        sections = [
            {
                "title": "Main Menu",
                "rows": [
                    {"id": "book", "title": "📅 Book Appointment", "description": "Schedule a new appointment"},
                    {"id": "order", "title": "🛒 Place Order", "description": "Order products or services"},
                    {"id": "status", "title": "📋 Check Status", "description": "Check order or appointment status"},
                    {"id": "hours", "title": "🕐 Business Hours", "description": "View our operating hours"},
                    {"id": "support", "title": "💬 Contact Support", "description": "Talk to our team"}
                ]
            }
        ]
        
        return await self.send_list_message(
            to=to,
            body_text=f"Welcome to {business_name}! How can we help you today?",
            button_text="Select Option",
            sections=sections,
            header="Main Menu"
        )
    
    def get_media_url(self, media_id: str) -> str:
        """Get URL for media file"""
        return f"{self.BASE_URL}/{self.API_VERSION}/{media_id}"
    
    async def download_media(self, media_id: str) -> Dict:
        """Download media file from WhatsApp"""
        
        try:
            # First get the media URL
            response = requests.get(
                f"{self.BASE_URL}/{self.API_VERSION}/{media_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                media_info = response.json()
                media_url = media_info.get("url")
                
                # Download the actual media
                media_response = requests.get(
                    media_url,
                    headers=self._get_headers()
                )
                
                return {
                    "success": True,
                    "content_type": media_response.headers.get("Content-Type"),
                    "data": media_response.content
                }
            
            return {"success": False, "error": "Failed to get media info"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
whatsapp_service = WhatsAppService()
