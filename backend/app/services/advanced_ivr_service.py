"""
Advanced IVR Service
Multi-level menu system, department routing, and after-hours handling
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime, time, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from enum import Enum
import json

from app.core.config import settings


class IVRState(Enum):
    """IVR conversation states"""
    GREETING = "greeting"
    MAIN_MENU = "main_menu"
    DEPARTMENT_SELECT = "department_select"
    SERVICE_SELECT = "service_select"
    APPOINTMENT_FLOW = "appointment_flow"
    ORDER_FLOW = "order_flow"
    SUPPORT_FLOW = "support_flow"
    AFTER_HOURS = "after_hours"
    TRANSFER = "transfer"
    END = "end"


class IVRMenu:
    """IVR Menu configuration"""
    
    def __init__(self, menu_id: str, prompt: str, options: Dict[str, Dict]):
        self.menu_id = menu_id
        self.prompt = prompt
        self.options = options
    
    def get_option(self, selection: str) -> Optional[Dict]:
        """Get option by DTMF selection or voice input"""
        return self.options.get(selection)
    
    def to_dict(self) -> Dict:
        return {
            "menu_id": self.menu_id,
            "prompt": self.prompt,
            "options": self.options
        }


class AdvancedIVRService:
    """Service for advanced IVR functionality"""
    
    # Default IVR menus
    DEFAULT_MENUS = {
        "main": IVRMenu(
            menu_id="main",
            prompt="Thank you for calling. For appointments, press 1. For orders, press 2. For billing, press 3. For general inquiries, press 4. To speak with a representative, press 0.",
            options={
                "1": {"action": "navigate", "target": "appointments"},
                "2": {"action": "navigate", "target": "orders"},
                "3": {"action": "navigate", "target": "billing"},
                "4": {"action": "navigate", "target": "inquiries"},
                "0": {"action": "transfer", "target": "representative"},
                "appointment": {"action": "navigate", "target": "appointments"},
                "appointments": {"action": "navigate", "target": "appointments"},
                "order": {"action": "navigate", "target": "orders"},
                "billing": {"action": "navigate", "target": "billing"},
                "inquiry": {"action": "navigate", "target": "inquiries"},
                "representative": {"action": "transfer", "target": "representative"},
                "operator": {"action": "transfer", "target": "representative"}
            }
        ),
        "appointments": IVRMenu(
            menu_id="appointments",
            prompt="For new appointments, press 1. To reschedule, press 2. To cancel, press 3. For appointment status, press 4. To return to main menu, press 9.",
            options={
                "1": {"action": "start_flow", "target": "book_appointment"},
                "2": {"action": "start_flow", "target": "reschedule"},
                "3": {"action": "start_flow", "target": "cancel_appointment"},
                "4": {"action": "start_flow", "target": "appointment_status"},
                "9": {"action": "navigate", "target": "main"},
                "new": {"action": "start_flow", "target": "book_appointment"},
                "reschedule": {"action": "start_flow", "target": "reschedule"},
                "cancel": {"action": "start_flow", "target": "cancel_appointment"},
                "status": {"action": "start_flow", "target": "appointment_status"}
            }
        ),
        "orders": IVRMenu(
            menu_id="orders",
            prompt="To place a new order, press 1. For order status, press 2. To modify an order, press 3. For pickup instructions, press 4. To return to main menu, press 9.",
            options={
                "1": {"action": "start_flow", "target": "new_order"},
                "2": {"action": "start_flow", "target": "order_status"},
                "3": {"action": "start_flow", "target": "modify_order"},
                "4": {"action": "start_flow", "target": "pickup_info"},
                "9": {"action": "navigate", "target": "main"},
                "new": {"action": "start_flow", "target": "new_order"},
                "place": {"action": "start_flow", "target": "new_order"},
                "status": {"action": "start_flow", "target": "order_status"},
                "modify": {"action": "start_flow", "target": "modify_order"},
                "pickup": {"action": "start_flow", "target": "pickup_info"}
            }
        ),
        "billing": IVRMenu(
            menu_id="billing",
            prompt="For billing inquiries, press 1. To make a payment, press 2. For payment status, press 3. To speak with billing, press 0. To return to main menu, press 9.",
            options={
                "1": {"action": "start_flow", "target": "billing_inquiry"},
                "2": {"action": "start_flow", "target": "make_payment"},
                "3": {"action": "start_flow", "target": "payment_status"},
                "0": {"action": "transfer", "target": "billing_department"},
                "9": {"action": "navigate", "target": "main"}
            }
        ),
        "inquiries": IVRMenu(
            menu_id="inquiries",
            prompt="For hours and location, press 1. For services, press 2. For general questions, press 3. To return to main menu, press 9.",
            options={
                "1": {"action": "provide_info", "target": "hours_location"},
                "2": {"action": "provide_info", "target": "services"},
                "3": {"action": "start_flow", "target": "general_questions"},
                "9": {"action": "navigate", "target": "main"}
            }
        )
    }
    
    def __init__(self):
        self.custom_menus = {}
    
    def is_business_open(
        self,
        db: Session,
        business_id: int,
        check_time: datetime = None
    ) -> Dict:
        """Check if business is currently open"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return {"is_open": False, "reason": "Business not found"}
        
        check_time = check_time or datetime.now(timezone.utc)
        operating_hours = business.operating_hours or {}
        
        # Get day of week
        day_name = check_time.strftime('%A').lower()
        day_hours = operating_hours.get(day_name, {})
        
        if day_hours.get('closed', False):
            return {
                "is_open": False,
                "reason": "closed_today",
                "message": f"We're closed today. Please call back tomorrow or leave a message."
            }
        
        # Parse open/close times
        try:
            open_time_str = day_hours.get('open', '09:00')
            close_time_str = day_hours.get('close', '17:00')
            
            open_time = datetime.strptime(open_time_str, '%H:%M').time()
            close_time = datetime.strptime(close_time_str, '%H:%M').time()
            
            current_time = check_time.time()
            
            # Handle overnight hours (e.g., bar closing at 2am)
            if close_time < open_time:
                # Business spans midnight
                is_open = current_time >= open_time or current_time <= close_time
            else:
                is_open = open_time <= current_time <= close_time
            
            if is_open:
                return {
                    "is_open": True,
                    "closes_at": close_time_str,
                    "message": None
                }
            else:
                return {
                    "is_open": False,
                    "reason": "outside_hours",
                    "message": f"We're currently closed. Our hours today are {open_time_str} to {close_time_str}. Please leave a message or call back during business hours."
                }
                
        except Exception as e:
            print(f"[IVR] Error parsing hours: {e}")
            return {"is_open": True, "reason": "error"}  # Default to open on error
    
    def get_after_hours_config(
        self,
        db: Session,
        business_id: int
    ) -> Dict:
        """Get after-hours configuration for a business"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return self._default_after_hours_config()
        
        settings_dict = business.settings or {}
        after_hours = settings_dict.get('after_hours', {})
        
        return {
            **self._default_after_hours_config(),
            **after_hours
        }
    
    def _default_after_hours_config(self) -> Dict:
        """Default after-hours configuration"""
        return {
            "enabled": True,
            "greeting": "Thank you for calling. We're currently closed.",
            "options": [
                {"key": "1", "action": "voicemail", "label": "Leave a message"},
                {"key": "2", "action": "callback", "label": "Request a callback"},
                {"key": "3", "action": "emergency", "label": "Emergency contact"}
            ],
            "voicemail_enabled": True,
            "callback_enabled": True,
            "emergency_number": None,
            "auto_callback_time": "09:00"  # Next business day callback time
        }
    
    def process_menu_selection(
        self,
        db: Session,
        business_id: int,
        menu_id: str,
        selection: str,
        session_state: Dict = None
    ) -> Dict:
        """Process a menu selection and return next action"""
        
        # Get menu (custom or default)
        menu = self.custom_menus.get(business_id, {}).get(menu_id) or self.DEFAULT_MENUS.get(menu_id)
        
        if not menu:
            return {
                "action": "error",
                "message": "Invalid menu selection. Please try again.",
                "menu_id": menu_id
            }
        
        # Normalize selection
        selection = selection.lower().strip()
        
        # Get option
        option = menu.get_option(selection)
        
        if not option:
            # Try fuzzy matching for voice input
            option = self._fuzzy_match_option(menu, selection)
        
        if not option:
            return {
                "action": "invalid",
                "message": f"I didn't understand that selection. {menu.prompt}",
                "menu_id": menu_id,
                "valid_options": list(menu.options.keys())[:5]  # Show first 5 valid options
            }
        
        return {
            **option,
            "previous_menu": menu_id
        }
    
    def _fuzzy_match_option(self, menu: IVRMenu, selection: str) -> Optional[Dict]:
        """Fuzzy match voice input to menu options"""
        selection_words = selection.split()
        
        for word in selection_words:
            for key, option in menu.options.items():
                # Check if word matches key or is similar
                if word in key or key in word:
                    return option
        
        return None
    
    def get_menu_prompt(
        self,
        db: Session,
        business_id: int,
        menu_id: str
    ) -> str:
        """Get the prompt for a menu"""
        menu = self.custom_menus.get(business_id, {}).get(menu_id) or self.DEFAULT_MENUS.get(menu_id)
        
        if menu:
            return menu.prompt
        
        return "Please make a selection."
    
    def create_custom_menu(
        self,
        db: Session,
        business_id: int,
        menu_config: Dict
    ) -> Dict:
        """Create a custom IVR menu for a business"""
        from app.models.models import Business
        
        if business_id not in self.custom_menus:
            self.custom_menus[business_id] = {}
        
        menu = IVRMenu(
            menu_id=menu_config['menu_id'],
            prompt=menu_config['prompt'],
            options=menu_config['options']
        )
        
        self.custom_menus[business_id][menu.menu_id] = menu
        
        # Save to business settings
        business = db.query(Business).filter(Business.id == business_id).first()
        if business:
            settings_dict = business.settings or {}
            ivr_menus = settings_dict.get('ivr_menus', {})
            ivr_menus[menu.menu_id] = menu.to_dict()
            settings_dict['ivr_menus'] = ivr_menus
            business.settings = settings_dict
            db.commit()
        
        return {"success": True, "menu_id": menu.menu_id}
    
    def get_ivr_flow(
        self,
        db: Session,
        business_id: int
    ) -> Dict:
        """Get complete IVR flow configuration"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        
        if business and business.settings:
            custom_menus = business.settings.get('ivr_menus', {})
            if custom_menus:
                return {
                    "menus": {k: IVRMenu(**v).to_dict() for k, v in custom_menus.items()},
                    "after_hours": business.settings.get('after_hours', self._default_after_hours_config())
                }
        
        return {
            "menus": {k: v.to_dict() for k, v in self.DEFAULT_MENUS.items()},
            "after_hours": self._default_after_hours_config()
        }
    
    def handle_dtmf_input(
        self,
        dtmf_sequence: str,
        session_state: Dict
    ) -> Dict:
        """Handle DTMF (keypad) input sequence"""
        
        # Handle common DTMF patterns
        if dtmf_sequence == "*":
            return {"action": "return_to_main", "menu_id": "main"}
        
        if dtmf_sequence == "#":
            return {"action": "end_call"}
        
        # Process as menu selection
        current_menu = session_state.get('current_menu', 'main')
        
        return {
            "action": "process_selection",
            "menu_id": current_menu,
            "selection": dtmf_sequence
        }
    
    def get_transfer_target(
        self,
        db: Session,
        business_id: int,
        department: str
    ) -> Optional[str]:
        """Get transfer phone number for a department"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        
        if business and business.settings:
            departments = business.settings.get('departments', {})
            dept_config = departments.get(department, {})
            return dept_config.get('phone_number')
        
        return None
    
    def schedule_callback(
        self,
        db: Session,
        business_id: int,
        customer_phone: str,
        preferred_time: datetime = None
    ) -> Dict:
        """Schedule a callback for the customer"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        
        # Get callback time from settings
        settings_dict = business.settings or {} if business else {}
        after_hours = settings_dict.get('after_hours', self._default_after_hours_config())
        callback_time_str = after_hours.get('auto_callback_time', '09:00')
        
        # Default to next business day at callback time
        if not preferred_time:
            now = datetime.now(timezone.utc)
            callback_time = datetime.strptime(callback_time_str, '%H:%M').time()
            preferred_time = datetime.combine(now.date(), callback_time)
            
            # If it's past callback time today, schedule for tomorrow
            if now.time() > callback_time:
                preferred_time += timedelta(days=1)
        
        # TODO: Create callback record in database and schedule job
        
        return {
            "success": True,
            "scheduled_time": preferred_time.isoformat(),
            "message": f"We'll call you back at {preferred_time.strftime('%I:%M %p')} on {preferred_time.strftime('%B %d')}."
        }
    
    def get_voicemail_greeting(
        self,
        db: Session,
        business_id: int
    ) -> str:
        """Get voicemail greeting for after-hours"""
        after_hours = self.get_after_hours_config(db, business_id)
        
        base_greeting = after_hours.get('greeting', 'Thank you for calling. We are currently closed.')
        
        options_text = "Press 1 to leave a message, press 2 to request a callback."
        
        if after_hours.get('emergency_number'):
            options_text += " Press 3 for emergency assistance."
        
        return f"{base_greeting} {options_text}"


# Singleton instance
advanced_ivr_service = AdvancedIVRService()
