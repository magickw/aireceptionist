"""
Business Type Templates - Configurable autonomous business operator platform
Powered by Amazon Nova reasoning and execution agents.

Architecture:
- Structured flow configuration (separate behavior from policy)
- Industry-specific risk profiles
- Autonomy level tuning
- Field validation schemas
- Cross-industry abstraction layer
- Database-driven templates with runtime configuration
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import re


# Import database service
try:
    from app.services.business_template_service import get_template
    DB_INTEGRATION_AVAILABLE = True
except ImportError:
    DB_INTEGRATION_AVAILABLE = False


class AutonomyLevel(str, Enum):
    """Autonomy levels for different business types"""
    HIGH = "high"        # Full autonomous operation allowed
    MEDIUM = "medium"    # Some actions require confirmation
    RESTRICTED = "restricted"  # Strict oversight, low confidence threshold for escalation


class GovernanceTier(str, Enum):
    """
    Governance tiers for action execution.
    This creates controlled autonomy instead of binary escalation.
    """
    AUTO = "auto"                      # Execute automatically, no oversight needed
    CONFIRM_BEFORE_EXECUTE = "confirm" # Ask user to confirm before executing
    PRIORITY_FLOW = "priority"         # Execute with safety instructions, then escalate
    HUMAN_REVIEW = "human_review"      # Pause for human approval before any action
    ESCALATE_IMMEDIATE = "escalate"    # Immediate transfer to human, AI provides initial response
    ADAPTIVE_MONITORING = "adaptive"    # Dynamic adjustment based on real-time conditions
    ENHANCED_OVERSIGHT = "enhanced"     # Extra oversight with explainable AI


class ActionRisk(str, Enum):
    """Risk classification for different actions"""
    LOW = "low"           # Information queries, general questions
    MEDIUM = "medium"     # Appointments, orders, standard operations  
    HIGH = "high"         # Financial, medical, legal actions
    CRITICAL = "critical" # Safety emergencies, legal urgency, medical emergencies


class FieldValidation:
    """Field validation helpers"""
    
    @staticmethod
    def validate_phone(value: str) -> bool:
        """Validate phone number format"""
        if not value:
            return False
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\+\.]', '', value)
        return len(cleaned) >= 10 and cleaned.isdigit()
    
    @staticmethod
    def validate_email(value: str) -> bool:
        """Validate email format"""
        if not value:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def validate_future_date(value: str) -> bool:
        """Validate that date is in the future"""
        from datetime import datetime, timezone
        from dateutil import parser as date_parser
        try:
            parsed = date_parser.parse(value, fuzzy=True)
            return parsed > datetime.now()
        except:
            return False
    
    @staticmethod
    def validate_string(value: str) -> bool:
        """Validate non-empty string"""
        return bool(value and value.strip())
    
    @staticmethod
    def validate_credit_card(value: str) -> bool:
        """Validate credit card number using Luhn algorithm"""
        if not value:
            return False
        # Remove spaces and dashes
        cleaned = re.sub(r'[\s-]', '', value)
        
        # Check if it's all digits and has valid length
        if not cleaned.isdigit() or len(cleaned) < 13 or len(cleaned) > 19:
            return False
        
        # Luhn algorithm
        total = 0
        reverse_digits = cleaned[::-1]
        
        for i, digit in enumerate(reverse_digits):
            d = int(digit)
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
        
        return total % 10 == 0
    
    @staticmethod
    def validate_address(value: str) -> bool:
        """Validate address format (basic check for street, city, state/zip)"""
        if not value or len(value.strip()) < 10:
            return False
        
        # Check for common address components
        has_number = bool(re.search(r'\d+', value))
        has_street = bool(re.search(r'\b(street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|way|court|ct|place|pl)\b', value.lower()))
        has_zip = bool(re.search(r'\b\d{5}(-\d{4})?\b', value))
        
        # At minimum, should have a number and one address component
        return has_number and (has_street or has_zip)
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> bool:
        """Validate that end_date is after start_date"""
        from datetime import datetime
        from dateutil import parser as date_parser
        try:
            start = date_parser.parse(start_date, fuzzy=True)
            end = date_parser.parse(end_date, fuzzy=True)
            return end > start
        except:
            return False
    
    @staticmethod
    def validate_currency(value: str) -> bool:
        """Validate currency amount (positive number with optional decimals)"""
        if not value:
            return False
        # Remove currency symbols and commas
        cleaned = re.sub(r'[$,€£¥]', '', value)
        try:
            amount = float(cleaned)
            return amount >= 0
        except ValueError:
            return False
    
    @staticmethod
    def validate_zip_code(value: str, country: str = "US") -> bool:
        """Validate ZIP/postal code format"""
        if not value:
            return False
        
        if country.upper() == "US":
            # US ZIP: 5 digits or 5-4 format
            return bool(re.match(r'^\d{5}(-\d{4})?$', value))
        elif country.upper() == "CA":
            # Canadian postal code: A1A 1A1
            return bool(re.match(r'^[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d$', value))
        elif country.upper() == "UK":
            # UK postcode: various formats
            return bool(re.match(r'^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$', value, re.IGNORECASE))
        else:
            # Generic: alphanumeric, 3-10 characters
            return bool(re.match(r'^[A-Za-z0-9\s-]{3,10}$', value))
    
    @staticmethod
    def validate_ssn(value: str) -> bool:
        """Validate US Social Security Number format"""
        if not value:
            return False
        # Remove common formatting
        cleaned = re.sub(r'[\s-]', '', value)
        return bool(re.match(r'^\d{9}$', cleaned))
    
    @staticmethod
    def validate_vin(value: str) -> bool:
        """Validate Vehicle Identification Number (VIN)"""
        if not value:
            return False
        # Remove common formatting
        cleaned = re.sub(r'[\s-]', '', value).upper()
        # VIN should be 17 characters, excluding I, O, Q
        if len(cleaned) != 17:
            return False
        if any(c in cleaned for c in 'IOQ'):
            return False
        return bool(re.match(r'^[A-HJ-NPR-Z0-9]{17}$', cleaned))
    
    @staticmethod
    def validate_age(value: str, min_age: int = 0, max_age: int = 150) -> bool:
        """Validate age is within reasonable range"""
        try:
            age = int(value)
            return min_age <= age <= max_age
        except ValueError:
            return False
    
    @staticmethod
    def validate_url(value: str) -> bool:
        """Validate URL format"""
        if not value:
            return False
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def validate_percentage(value: str) -> bool:
        """Validate percentage value (0-100 or 0-1)"""
        if not value:
            return False
        try:
            # Remove % sign if present
            cleaned = value.replace('%', '')
            num = float(cleaned)
            return 0 <= num <= 100
        except ValueError:
            return False
    
    @staticmethod
    def validate_policy_number(value: str) -> bool:
        """Validate insurance policy number (alphanumeric, 5-20 chars)"""
        if not value:
            return False
        cleaned = re.sub(r'[\s-]', '', value)
        return bool(re.match(r'^[A-Za-z0-9]{5,20}$', cleaned))
    
    @staticmethod
    def validate_account_number(value: str) -> bool:
        """Validate bank account number (8-17 digits)"""
        if not value:
            return False
        cleaned = re.sub(r'[\s-]', '', value)
        return bool(re.match(r'^\d{8,17}$', cleaned))
    
    @staticmethod
    def validate_routing_number(value: str) -> bool:
        """Validate US routing number (9 digits)"""
        if not value:
            return False
        cleaned = re.sub(r'[\s-]', '', value)
        if len(cleaned) != 9 or not cleaned.isdigit():
            return False
        
        # Validate routing number checksum
        digits = [int(d) for d in cleaned]
        weights = [3, 7, 1, 3, 7, 1, 3, 7, 1]
        total = sum(d * w for d, w in zip(digits, weights))
        return total % 10 == 0


class BusinessTypeTemplate:
    """Template for different business types with structured configuration"""
    
    # Validation type mapping
    VALIDATORS = {
        "string": FieldValidation.validate_string,
        "phone": FieldValidation.validate_phone,
        "email": FieldValidation.validate_email,
        "future_date": FieldValidation.validate_future_date,
        "credit_card": FieldValidation.validate_credit_card,
        "address": FieldValidation.validate_address,
        "currency": FieldValidation.validate_currency,
        "zip_code": FieldValidation.validate_zip_code,
        "ssn": FieldValidation.validate_ssn,
        "vin": FieldValidation.validate_vin,
        "age": FieldValidation.validate_age,
        "url": FieldValidation.validate_url,
        "percentage": FieldValidation.validate_percentage,
        "policy_number": FieldValidation.validate_policy_number,
        "account_number": FieldValidation.validate_account_number,
        "routing_number": FieldValidation.validate_routing_number,
    }
    
    # Pre-defined business types with their characteristics
    TEMPLATES: Dict[str, Dict[str, Any]] = {
        # ============================================================
        # RESTAURANT - High Autonomy
        # ============================================================
        "restaurant": {
            "name": "Restaurant",
            "icon": "restaurant",
            "autonomy_level": AutonomyLevel.HIGH,
            "risk_profile": {
                "high_risk_intents": ["refund_request", "food_allergy"],
                "auto_escalate_threshold": 0.7,
                "confidence_threshold": 0.5,
            },
            "common_intents": [
                "make_reservation", "order_food", "menu_inquiry", 
                "dietary_options", "hours_inquiry", "location_inquiry",
                "special_events", "catering", "wait_time", "pricing_inquiry",
                "location_directions", "make_payment"
            ],
            "fields": {
                "customer_name": {"required": False, "validation": "string", "prompt": "May I have your name for the order?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
                "party_size": {"required": True, "validation": "string", "prompt": "How many guests will be joining?"},
                "date": {"required": True, "validation": "future_date", "prompt": "What date would you like?"},
                "time": {"required": True, "validation": "string", "prompt": "What time works best for you?"},
                "menu_item": {"required": False, "validation": "string", "prompt": "What would you like to order?"},
                "quantity": {"required": False, "validation": "string", "prompt": "How many?"},
                "delivery_method": {"required": False, "validation": "string", "prompt": "Would you like that for pickup or delivery?"},
                "special_requests": {"required": False, "validation": "string", "prompt": "Any special requests or modifications?"},
            },
            "order_food_flow": {
                "type": "order",
                "steps": [
                    {"field": "menu_item", "ask_if_missing": True},
                    {"field": "quantity", "ask_if_missing": False, "default": 1},
                    {"field": "special_requests", "ask_if_missing": True},
                    {"intent": "add_drink", "prompt": "Would you like to add a drink with that?"},
                    {"intent": "add_side", "prompt": "Would you like any sides to go with your order?"},
                    {"field": "delivery_method", "ask_if_missing": True},
                    {"field": "customer_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                ],
                "final_action": "CONFIRM_ORDER",
                "confirmation_message": "Your order for {menu_item} is confirmed. Your total is ${total}. It will be ready for {delivery_method} shortly.",
            },
            "reservation_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "party_size", "ask_if_missing": True},
                    {"field": "date", "ask_if_missing": True},
                    {"field": "time", "ask_if_missing": True},
                    {"field": "customer_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
            },
            "system_prompt_addition": """
## Restaurant-Specific Guidelines:
- **Advanced Ordering Flow**: When a user wants to order food, follow the `order_food_flow`.
- First, get their main `menu_item`. After they choose an item, ask for any `special_requests`.
- **Upselling**: After handling special requests, ask if they want to add a drink or a side. Be natural, e.g., "Would you like a drink or a side to go with that?"
- After the full order is assembled, then ask for the `delivery_method` (pickup or delivery).
- Finally, once the order details are complete, collect the `customer_name` and `phone`.
- Use the `CONFIRM_ORDER` action only after all items, upsells, and contact info are collected.
- **Pricing**: When customers ask about prices, provide the EXACT price from the Menu. For multiple items, ALWAYS calculate and state the TOTAL price before finalizing.
- **DO NOT** repeat questions. If you have the information (e.g., they already said "for pickup"), move to the next step.
""",
            "example_responses": {
                "reservation": "I'd be happy to help you reserve a table. How many guests will be joining?",
                "order": "Great choice! Would you like that for here or to go?",
                "pricing": "Our fried rice is $12.99. Would you like to order that?",
            }
        },
        
        # ============================================================
        # HOTEL - Medium Autonomy
        # ============================================================
        "hotel": {
            "name": "Hotel",
            "icon": "hotel",
            "autonomy_level": AutonomyLevel.MEDIUM,
            "risk_profile": {
                "high_risk_intents": ["billing_dispute", "safety_concern"],
                "auto_escalate_threshold": 0.6,
                "confidence_threshold": 0.6,
            },
            "common_intents": [
                "book_room", "check_availability", "amenities_inquiry",
                "check_in_out", "room_service", "pool_gym", "wifi_password",
                "late_checkout", "early_checkin", "parking", "pet_policy",
                "conference_rooms", "airport_shuttle", "breakfast_included",
                "extend_stay"
            ],
            "fields": {
                "customer_name": {"required": True, "validation": "string", "prompt": "May I have the name for the reservation?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's a contact number for the booking confirmation?"},
                "check_in_date": {"required": True, "validation": "future_date", "prompt": "What's your check-in date?"},
                "check_out_date": {"required": True, "validation": "future_date", "prompt": "What's your check-out date?"},
                "room_type": {"required": True, "validation": "string", "prompt": "What room type would you prefer? (standard, deluxe, suite)"},
                "number_of_guests": {"required": True, "validation": "string", "prompt": "How many guests?"},
                # Extend stay specific fields
                "room_number": {"required": True, "validation": "string", "prompt": "What's your room number?"},
                "extension_days": {"required": False, "validation": "string", "prompt": "How many days would you like to extend?"},
                "new_checkout_date": {"required": False, "validation": "future_date", "prompt": "What would be your new check-out date?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "check_in_date", "ask_if_missing": True},
                    {"field": "check_out_date", "ask_if_missing": True},
                    {"field": "room_type", "ask_if_missing": True},
                    {"field": "number_of_guests", "ask_if_missing": True},
                    {"field": "customer_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Your reservation is confirmed for {check_in_date} to {check_out_date}, {room_type}. Total: ${total}.",
            },
            "system_prompt_addition": """
## Hotel-Specific Guidelines:
- Know room types and current rates.
- Handle booking modifications and cancellations.
- Provide information about amenities (pool, gym, spa, restaurant).
- Assist with check-in/check-out processes.
- Handle room service orders.
- Know policy on late checkout, early check-in.
- Answer questions about parking, WiFi, pet policies.
- Handle corporate account and group bookings.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" info repeatedly** - If customer already confirmed, move on.
- **DO NOT repeat rates** - Mention room rates once.
""",
            "example_responses": {
                "booking": "I'd be happy to help you book a room. What dates are you looking at?",
                "amenities": "Our hotel features a fitness center, outdoor pool, on-site restaurant, and free WiFi.",
                "confirm": "Your reservation is confirmed. See you soon!",
                "extend_stay": "I'd be happy to help you extend your stay. Could you please provide your name and room number so I can look up your reservation?",
            }
        },
        
        # ============================================================
        # DENTAL CLINIC - Restricted Autonomy (Healthcare)
        # ============================================================
        "dental": {
            "name": "Dental Clinic",
            "icon": "medical_services",
            "autonomy_level": AutonomyLevel.RESTRICTED,
            "risk_profile": {
                "high_risk_intents": ["medical_emergency", "severe_pain", "insurance_dispute"],
                "auto_escalate_threshold": 0.4,  # Lower threshold - escalate sooner
                "confidence_threshold": 0.8,  # Higher threshold - need more confidence
            },
            "common_intents": [
                "book_appointment", "emergency_dental", "checkup_cleaning",
                "cosmetic_dentistry", "insurance_inquiry", "new_patient",
                "tooth_pain", "whitening", "cavity", "root_canal"
            ],
            "fields": {
                "patient_name": {"required": True, "validation": "string", "prompt": "May I have your full name for the appointment?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best phone number to reach you?"},
                "service_type": {"required": True, "validation": "string", "prompt": "What dental service do you need? (cleaning, checkup, emergency, etc.)"},
                "preferred_date": {"required": True, "validation": "future_date", "prompt": "What date works best for you?"},
                "preferred_time": {"required": True, "validation": "string", "prompt": "What time of day works best?"},
                "insurance_provider": {"required": False, "validation": "string", "prompt": "Do you have dental insurance?"},
                "symptoms": {"required": False, "validation": "string", "prompt": "Can you describe your symptoms?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "patient_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "service_type", "ask_if_missing": True},
                    {"field": "symptoms", "ask_if_missing": False, "for_intents": ["emergency_dental", "tooth_pain"]},
                    {"field": "preferred_date", "ask_if_missing": True},
                    {"field": "preferred_time", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Your dental appointment is confirmed for {preferred_date} at {preferred_time}. Please arrive 15 minutes early.",
            },
            "system_prompt_addition": """
## Dental Clinic-Specific Guidelines:
- HIPAA compliance required for all patient information.
- For dental emergencies, prioritize and mention same-day availability.
- Handle insurance inquiries professionally.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" phone numbers** - If patient provides phone, accept it and move on.
- **DO NOT ask to "verify" information** - Trust what the patient tells you.
- For severe pain or emergencies, consider escalation to human staff.
""",
            "example_responses": {
                "appointment": "I'll schedule you for a checkup. What date works best?",
                "emergency": "We have same-day emergency appointments. Can you describe your symptoms?",
                "confirm": "I've scheduled your dental appointment. Please arrive 15 minutes early.",
            }
        },
        
        # ============================================================
        # MEDICAL CLINIC - Restricted Autonomy (Healthcare)
        # ============================================================
        "medical": {
            "name": "Medical Clinic",
            "icon": "local_hospital",
            "autonomy_level": AutonomyLevel.RESTRICTED,
            "risk_profile": {
                "high_risk_intents": ["medical_emergency", "severe_symptoms", "prescription_issue", "lab_results_inquiry"],
                "auto_escalate_threshold": 0.3,  # Very low - escalate quickly for medical
                "confidence_threshold": 0.85,
            },
            "common_intents": [
                "book_appointment", "symptoms_inquiry", "prescription_refill",
                "lab_results", "insurance_inquiry", "new_patient",
                "urgent_care", "telehealth", "vaccinations", "specialist_referral"
            ],
            "fields": {
                "patient_name": {"required": True, "validation": "string", "prompt": "May I have your full name?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
                "date": {"required": True, "validation": "future_date", "prompt": "What date works for your appointment?"},
                "time": {"required": True, "validation": "string", "prompt": "What time works best?"},
                "reason_for_visit": {"required": True, "validation": "string", "prompt": "What's the reason for your visit?"},
                "symptoms": {"required": False, "validation": "string", "prompt": "Can you briefly describe your symptoms?"},
                "insurance_provider": {"required": False, "validation": "string", "prompt": "Do you have insurance?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "patient_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "reason_for_visit", "ask_if_missing": True},
                    {"field": "symptoms", "ask_if_missing": False, "for_intents": ["symptoms_inquiry", "urgent_care"]},
                    {"field": "date", "ask_if_missing": True},
                    {"field": "time", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Your appointment is confirmed for {date} at {time}. We'll send a confirmation to your phone.",
            },
            "system_prompt_addition": """
## Medical Clinic-Specific Guidelines:
- HIPAA compliance REQUIRED for all patient information.
- Triage symptoms to determine urgency.
- For medical emergencies, escalate to human staff immediately.
- **DO NOT provide medical advice** - Only schedule and collect information.
- **DO NOT repeat questions** - Track what has been collected.
- **DO NOT ask to "confirm" phone numbers** - If patient provides phone, accept it and move on.
- **DO NOT ask to "verify" information** - Trust what the patient tells you.
""",
            "example_responses": {
                "appointment": "I can schedule you with one of our providers. What type of visit do you need?",
                "symptoms": "Can you briefly describe your symptoms?",
                "prescription": "For prescription refills, please allow 24-48 hours. Which pharmacy?",
            }
        },
        
        # ============================================================
        # LAW FIRM - Restricted Autonomy (Legal)
        # ============================================================
        "law_firm": {
            "name": "Law Firm",
            "icon": "gavel",
            "autonomy_level": AutonomyLevel.RESTRICTED,
            "risk_profile": {
                "high_risk_intents": ["legal_advice", "criminal_matter", "urgent_court_date", "confidential_matter"],
                "auto_escalate_threshold": 0.4,
                "confidence_threshold": 0.8,
            },
            "common_intents": [
                "consultation_request", "case_evaluation", "legal_advice",
                "family_law", "criminal_defense", "real_estate_law", "business_law",
                "immigration", "personal_injury", "divorce", "contract_review"
            ],
            "fields": {
                "client_name": {"required": True, "validation": "string", "prompt": "May I have your name for our records?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number for our attorney to reach you?"},
                "legal_matter_type": {"required": True, "validation": "string", "prompt": "What area of law does your matter involve? (family, criminal, business, etc.)"},
                "brief_case_description": {"required": True, "validation": "string", "prompt": "Could you briefly describe your legal matter?"},
                "preferred_date": {"required": True, "validation": "future_date", "prompt": "When would you like to schedule your consultation?"},
                "preferred_time": {"required": True, "validation": "string", "prompt": "What time works best?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "client_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "legal_matter_type", "ask_if_missing": True},
                    {"field": "brief_case_description", "ask_if_missing": True},
                    {"field": "preferred_date", "ask_if_missing": True},
                    {"field": "preferred_time", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Your consultation is confirmed for {preferred_date} at {preferred_time}. Everything discussed is protected by attorney-client privilege.",
            },
            "system_prompt_addition": """
## Law Firm-Specific Guidelines:
- Determine the area of law needed (family, criminal, business, etc.).
- Collect basic case information for attorney matching.
- Schedule initial consultations.
- Explain attorney-client privilege.
- Know billing structure (hourly, flat fee, contingency).
- Handle urgent legal matters with priority.
- Maintain confidentiality in all communications.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" info repeatedly** - If customer already confirmed, move on.
""",
            "example_responses": {
                "consultation": "I'd be happy to schedule a consultation. What area of law does your matter involve?",
                "areas": "Our firm handles family law, criminal defense, business law, personal injury, and more.",
                "urgent": "I understand this is urgent. Let me get you scheduled as soon as possible.",
            }
        },
        
        # ============================================================
        # SALON / SPA - High Autonomy
        # ============================================================
        "salon": {
            "name": "Salon / Spa",
            "icon": "content_cut",
            "autonomy_level": AutonomyLevel.HIGH,
            "risk_profile": {
                "high_risk_intents": ["allergic_reaction", "service_complaint"],
                "auto_escalate_threshold": 0.7,
                "confidence_threshold": 0.5,
            },
            "common_intents": [
                "book_appointment", "haircut", "coloring", "styling",
                "nails", "massage", "facial", "spa_package",
                "products_inquiry", "stylist_preference", "bride_package"
            ],
            "fields": {
                "customer_name": {"required": True, "validation": "string", "prompt": "May I have your name for the appointment?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number for your appointment confirmation?"},
                "service_type": {"required": True, "validation": "string", "prompt": "What service are you looking for?"},
                "stylist_preference": {"required": False, "validation": "string", "prompt": "Do you have a stylist preference?"},
                "preferred_date": {"required": True, "validation": "future_date", "prompt": "What date works for you?"},
                "preferred_time": {"required": True, "validation": "string", "prompt": "What time works best?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "service_type", "ask_if_missing": True},
                    {"field": "stylist_preference", "ask_if_missing": False},
                    {"field": "customer_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "preferred_date", "ask_if_missing": True},
                    {"field": "preferred_time", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "You're all set! Your appointment for {service_type} is on {preferred_date} at {preferred_time}.",
            },
            "system_prompt_addition": """
## Salon/Spa-Specific Guidelines:
- Know all services and their durations/pricing.
- For multiple services, calculate total time.
- **DO NOT repeat pricing** - Mention prices once.
- Suggest complementary services when appropriate.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" info repeatedly** - If customer already confirmed, move on.
- **DO NOT repeat pricing** - Mention service prices once.
""",
            "example_responses": {
                "booking": "What service are you looking for?",
                "stylist": "Do you have a stylist preference?",
                "confirm": "You're all set! See you on {preferred_date}.",
            }
        },
        
        # ============================================================
        # FITNESS / GYM - High Autonomy
        # ============================================================
        "fitness": {
            "name": "Fitness Center / Gym",
            "icon": "fitness_center",
            "autonomy_level": AutonomyLevel.HIGH,
            "risk_profile": {
                "high_risk_intents": ["injury_report", "equipment_issue", "billing_dispute"],
                "auto_escalate_threshold": 0.6,
                "confidence_threshold": 0.5,
            },
            "common_intents": [
                "membership_signup", "class_booking", "trainer_booking",
                "membership_freeze", "membership_cancel", "billing_inquiry",
                "hours_inquiry", "tour_request", "personal_training", "group_classes"
            ],
            "fields": {
                "customer_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
                "email": {"required": True, "validation": "email", "prompt": "What's your email address?"},
                "membership_type": {"required": False, "validation": "string", "prompt": "Which membership plan interests you?"},
                "class_name": {"required": False, "validation": "string", "prompt": "Which class would you like to book?"},
                "trainer_preference": {"required": False, "validation": "string", "prompt": "Do you have a trainer preference?"},
                "preferred_date": {"required": False, "validation": "future_date", "prompt": "What date works for you?"},
                "preferred_time": {"required": False, "validation": "string", "prompt": "What time works best?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "customer_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "email", "ask_if_missing": True},
                    {"field": "class_name", "ask_if_missing": False, "for_intents": ["class_booking"]},
                    {"field": "trainer_preference", "ask_if_missing": False, "for_intents": ["trainer_booking", "personal_training"]},
                    {"field": "preferred_date", "ask_if_missing": True},
                    {"field": "preferred_time", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "You're booked for {class_name} on {preferred_date} at {preferred_time}. See you there!",
            },
            "system_prompt_addition": """
## Fitness Center-Specific Guidelines:
- Handle membership signups, class bookings, and personal training.
- Know class schedules, trainer availability, and membership tiers.
- For membership cancellations, follow retention protocol.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" info repeatedly** - If customer already confirmed, move on.
- **DO NOT repeat pricing** - Mention rates once.
- Suggest appropriate membership tiers based on customer needs.
""",
            "example_responses": {
                "membership": "We have several membership options. Are you interested in basic, premium, or all-access?",
                "class_booking": "Which class would you like to book? We have yoga, spin, HIIT, and more.",
                "trainer": "Would you like to book a session with one of our personal trainers?",
            }
        },
        
        # ============================================================
        # REAL ESTATE - Medium Autonomy
        # ============================================================
        "real_estate": {
            "name": "Real Estate Agency",
            "icon": "home",
            "autonomy_level": AutonomyLevel.MEDIUM,
            "risk_profile": {
                "high_risk_intents": ["legal_question", "contract_issue", "buyer_seller_dispute"],
                "auto_escalate_threshold": 0.5,
                "confidence_threshold": 0.6,
            },
            "common_intents": [
                "property_inquiry", "schedule_showing", "mortgage_referral",
                "rental_application", "listing_inquiry", "market_analysis",
                "seller_consultation", "buyer_consultation", "open_house"
            ],
            "fields": {
                "client_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
                "email": {"required": True, "validation": "email", "prompt": "What's your email address?"},
                "property_interest": {"required": False, "validation": "string", "prompt": "Are you looking to buy, sell, or rent?"},
                "property_address": {"required": False, "validation": "string", "prompt": "Which property are you interested in?"},
                "budget_range": {"required": False, "validation": "string", "prompt": "What's your budget range?"},
                "preferred_date": {"required": False, "validation": "future_date", "prompt": "When would you like to schedule a showing?"},
                "preferred_time": {"required": False, "validation": "string", "prompt": "What time works best?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "client_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "email", "ask_if_missing": True},
                    {"field": "property_interest", "ask_if_missing": True},
                    {"field": "property_address", "ask_if_missing": False, "for_intents": ["property_inquiry", "schedule_showing"]},
                    {"field": "preferred_date", "ask_if_missing": True},
                    {"field": "preferred_time", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Your showing for {property_address} is confirmed for {preferred_date} at {preferred_time}. An agent will meet you there.",
            },
            "system_prompt_addition": """
## Real Estate-Specific Guidelines:
- Handle property inquiries, showing scheduling, and consultations.
- Connect buyers with mortgage referral partners when appropriate.
- **DO NOT provide legal advice** - Only schedule and provide listing info.
- Know current listings and their details.
- For buyer/seller disputes, escalate to agent.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" info repeatedly** - If customer already confirmed, move on.
""",
            "example_responses": {
                "property_inquiry": "I'd be happy to tell you about that property. What would you like to know?",
                "showing": "I can schedule a showing for you. What date and time work best?",
                "consultation": "Would you like to schedule a consultation with one of our agents?",
            }
        },
        
        # ============================================================
        # HVAC / HOME SERVICES - Medium Autonomy
        # ============================================================
        "hvac": {
            "name": "HVAC / Home Services",
            "icon": "hvac",
            "autonomy_level": AutonomyLevel.MEDIUM,
            "risk_profile": {
                "high_risk_intents": ["gas_leak", "emergency_repair", "safety_concern", "carbon_monoxide"],
                "auto_escalate_threshold": 0.4,  # Low for safety issues
                "confidence_threshold": 0.6,
            },
            "common_intents": [
                "emergency_repair", "schedule_service", "estimate_request",
                "seasonal_maintenance", "warranty_inquiry", "installation_quote",
                "hvac_repair", "plumbing", "electrical"
            ],
            "fields": {
                "customer_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
                "address": {"required": True, "validation": "string", "prompt": "What's the service address?"},
                "service_type": {"required": True, "validation": "string", "prompt": "What type of service do you need?"},
                "issue_description": {"required": False, "validation": "string", "prompt": "Can you describe the issue?"},
                "preferred_date": {"required": False, "validation": "future_date", "prompt": "When would you like us to come?"},
                "preferred_time": {"required": False, "validation": "string", "prompt": "Morning, afternoon, or evening?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "customer_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "address", "ask_if_missing": True},
                    {"field": "service_type", "ask_if_missing": True},
                    {"field": "issue_description", "ask_if_missing": False},
                    {"field": "preferred_date", "ask_if_missing": True},
                    {"field": "preferred_time", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Your service appointment is confirmed for {preferred_date} during the {preferred_time}. We'll call before arrival.",
            },
            "system_prompt_addition": """
## HVAC/Home Services-Specific Guidelines:
- For emergencies (gas leak, carbon monoxide), advise customer to evacuate and call emergency services.
- Handle emergency repairs with priority scheduling.
- Provide cost estimates when possible.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" info repeatedly** - If customer already confirmed, move on.
- **DO NOT repeat estimates** - Mention once.
- Know warranty coverage for common brands.
""",
            "example_responses": {
                "service": "What type of service do you need? We handle HVAC, plumbing, and electrical.",
                "emergency": "For gas leaks or carbon monoxide, please evacuate immediately and call 911. I'll dispatch an emergency technician right away.",
                "estimate": "I can have a technician come out for a free estimate. When works for you?",
            }
        },
        
        # ============================================================
        # ACCOUNTING / TAX FIRM - Restricted Autonomy
        # ============================================================
        "accounting": {
            "name": "Accounting / Tax Firm",
            "icon": "account_balance",
            "autonomy_level": AutonomyLevel.RESTRICTED,
            "risk_profile": {
                "high_risk_intents": ["tax_advice", "irs_notice", "audit", "legal_question"],
                "auto_escalate_threshold": 0.5,
                "confidence_threshold": 0.75,
            },
            "common_intents": [
                "tax_consultation", "document_upload", "filing_deadline",
                "irs_notice_handling", "bookkeeping_inquiry", "payroll_service",
                "business_accounting", "tax_return_status"
            ],
            "fields": {
                "client_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
                "email": {"required": True, "validation": "email", "prompt": "What's your email address?"},
                "service_type": {"required": True, "validation": "string", "prompt": "What service do you need? (tax prep, bookkeeping, payroll, etc.)"},
                "tax_year": {"required": False, "validation": "string", "prompt": "Which tax year?"},
                "business_type": {"required": False, "validation": "string", "prompt": "Is this for personal or business taxes?"},
                "preferred_date": {"required": True, "validation": "future_date", "prompt": "When would you like to schedule your consultation?"},
                "preferred_time": {"required": True, "validation": "string", "prompt": "What time works best?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "client_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "email", "ask_if_missing": True},
                    {"field": "service_type", "ask_if_missing": True},
                    {"field": "tax_year", "ask_if_missing": False, "for_intents": ["tax_consultation", "tax_return_status"]},
                    {"field": "preferred_date", "ask_if_missing": True},
                    {"field": "preferred_time", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Your consultation is confirmed for {preferred_date} at {preferred_time}. Please bring any relevant tax documents.",
            },
            "system_prompt_addition": """
## Accounting/Tax Firm-Specific Guidelines:
- **DO NOT provide specific tax advice** - Only schedule consultations.
- Know filing deadlines and remind clients appropriately.
- For IRS notices, schedule urgent consultation.
- Handle document upload instructions.
- Maintain confidentiality per professional standards.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" info repeatedly** - If customer already confirmed, move on.
""",
            "example_responses": {
                "consultation": "I can schedule a consultation with one of our accountants. What type of service do you need?",
                "deadline": "The filing deadline is April 15th. Would you like to schedule an appointment before then?",
                "irs_notice": "For IRS notices, I recommend scheduling an urgent consultation. When are you available?",
            }
        },
        
        # ============================================================
        # RETAIL - High Autonomy
        # ============================================================
        "retail": {
            "name": "Retail Store",
            "icon": "shopping_bag",
            "autonomy_level": AutonomyLevel.HIGH,
            "risk_profile": {
                "high_risk_intents": ["refund_dispute", "fraud_report", "safety_concern"],
                "auto_escalate_threshold": 0.6,
                "confidence_threshold": 0.5,
            },
            "common_intents": [
                "product_inquiry", "price_check", "store_hours",
                "return_policy", "loyalty_program", "gift_cards",
                "inventory_check", "online_order", "store_location"
            ],
            "fields": {
                "product_name": {"required": False, "validation": "string", "prompt": "Which product are you interested in?"},
                "quantity": {"required": False, "validation": "string", "prompt": "How many?"},
            },
            "system_prompt_addition": """
## Retail Store-Specific Guidelines:
- Know product inventory and pricing.
- Handle returns and exchanges per policy.
- Explain loyalty program benefits.
- Process gift card inquiries and purchases.
- Handle online order pickups.
- Know current promotions and sales.
- Direct to appropriate department if needed.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" info repeatedly** - If customer already confirmed, move on.
""",
            "example_responses": {
                "product": "Let me check our inventory for that item.",
                "returns": "Our return policy is 30 days with receipt. Do you have the receipt?",
                "loyalty": "Our loyalty program offers points for every purchase and exclusive member discounts!",
            }
        },
        
        # ============================================================
        # AUTO REPAIR - Medium Autonomy
        # ============================================================
        "auto_repair": {
            "name": "Auto Repair",
            "icon": "directions_car",
            "autonomy_level": AutonomyLevel.MEDIUM,
            "risk_profile": {
                "high_risk_intents": ["safety_recall", "brake_failure", "steering_issue"],
                "auto_escalate_threshold": 0.5,
                "confidence_threshold": 0.6,
            },
            "common_intents": [
                "schedule_service", "oil_change", "tire_rotation",
                "brake_service", "engine_check", "diagnostics",
                "appointment_status", "warranty_inquiry", "cost_estimate"
            ],
            "fields": {
                "customer_name": {"required": True, "validation": "string", "prompt": "May I have your name for the appointment?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you when your car is ready?"},
                "vehicle_info": {"required": True, "validation": "string", "prompt": "What's the make, model, and year of your vehicle?"},
                "service_type": {"required": True, "validation": "string", "prompt": "What type of service does your vehicle need?"},
                "preferred_date": {"required": True, "validation": "future_date", "prompt": "When would you like to bring your car in?"},
                "preferred_time": {"required": True, "validation": "string", "prompt": "What time works best?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "vehicle_info", "ask_if_missing": True},
                    {"field": "service_type", "ask_if_missing": True},
                    {"field": "customer_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "preferred_date", "ask_if_missing": True},
                    {"field": "preferred_time", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Your appointment is set for {preferred_date} at {preferred_time}. We'll call you with an estimate after inspection.",
            },
            "system_prompt_addition": """
## Auto Repair-Specific Guidelines:
- Collect vehicle information (make, model, year, mileage).
- Determine the type of service needed.
- Provide cost estimates when possible.
- Explain warranty coverage.
- Schedule appointments based on service duration.
- Handle towing and rental car inquiries.
- Update on repair status.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" info repeatedly** - If customer already confirmed, move on.
- **DO NOT repeat estimates** - Mention estimate price once.
- INTENT FILTERING: If customer asks for food/orders, politely redirect that this is an auto repair shop, not a restaurant. Suggest they contact a restaurant.
""",
            "example_responses": {
                "service": "What type of service does your vehicle need?",
                "estimate": "I can provide an estimate once our technicians examine the vehicle.",
                "appointment": "When would you like to bring your car in?",
            }
        },
        
        # ============================================================
        # EDUCATION / TUTORING - High Autonomy
        # ============================================================
        "education": {
            "name": "Education / Tutoring Center",
            "icon": "school",
            "autonomy_level": AutonomyLevel.HIGH,
            "risk_profile": {
                "high_risk_intents": ["safety_concern", "billing_dispute"],
                "auto_escalate_threshold": 0.6,
                "confidence_threshold": 0.5,
            },
            "common_intents": [
                "class_enrollment", "trial_session", "pricing_packages",
                "parent_inquiry", "tutor_booking", "schedule_change",
                "progress_report", "summer_program"
            ],
            "fields": {
                "parent_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
                "email": {"required": True, "validation": "email", "prompt": "What's your email address?"},
                "student_name": {"required": True, "validation": "string", "prompt": "What's your child's name?"},
                "student_grade": {"required": False, "validation": "string", "prompt": "What grade is your child in?"},
                "subject": {"required": True, "validation": "string", "prompt": "What subject would you like tutoring for?"},
                "preferred_date": {"required": False, "validation": "future_date", "prompt": "When would you like to start?"},
                "preferred_time": {"required": False, "validation": "string", "prompt": "What days and times work best?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "parent_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "email", "ask_if_missing": True},
                    {"field": "student_name", "ask_if_missing": True},
                    {"field": "subject", "ask_if_missing": True},
                    {"field": "preferred_date", "ask_if_missing": True},
                    {"field": "preferred_time", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Your trial session for {subject} is confirmed for {preferred_date} at {preferred_time}. We're excited to meet {student_name}!",
            },
            "system_prompt_addition": """
## Education/Tutoring-Specific Guidelines:
- Handle class enrollment, trial sessions, and tutor bookings.
- Know pricing packages and subject offerings.
- Be patient and helpful with parent inquiries.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" info repeatedly** - If customer already confirmed, move on.
- **DO NOT repeat pricing** - Mention once.
""",
            "example_responses": {
                "enrollment": "I'd be happy to help with enrollment. What subject are you interested in?",
                "trial": "We offer a free trial session! When would you like to schedule it?",
                "subjects": "We offer tutoring in math, reading, writing, science, and test prep.",
            }
        },
        
        # ============================================================
        # PET SERVICES - High Autonomy
        # ============================================================
        "pet_services": {
            "name": "Pet Services",
            "icon": "pets",
            "autonomy_level": AutonomyLevel.HIGH,
            "risk_profile": {
                "high_risk_intents": ["medical_emergency", "lost_pet", "aggressive_behavior"],
                "auto_escalate_threshold": 0.6,
                "confidence_threshold": 0.5,
            },
            "common_intents": [
                "book_grooming", "book_boarding", "vet_appointment",
                "vaccination_inquiry", "pricing_inquiry", "hours_inquiry",
                "pet_walking", "training_session", "emergency_vet"
            ],
            "fields": {
                "customer_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
                "pet_name": {"required": True, "validation": "string", "prompt": "What's your pet's name?"},
                "pet_type": {"required": True, "validation": "string", "prompt": "What kind of pet is it? (dog, cat, etc.)"},
                "service_type": {"required": True, "validation": "string", "prompt": "What service do you need?"},
                "preferred_date": {"required": True, "validation": "future_date", "prompt": "What date works for you?"},
                "preferred_time": {"required": True, "validation": "string", "prompt": "What time works best?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "pet_name", "ask_if_missing": True},
                    {"field": "pet_type", "ask_if_missing": True},
                    {"field": "service_type", "ask_if_missing": True},
                    {"field": "customer_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "preferred_date", "ask_if_missing": True},
                    {"field": "preferred_time", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Confirmed! {pet_name} is scheduled for {service_type} on {preferred_date} at {preferred_time}.",
            },
            "system_prompt_addition": """
## Pet Services-Specific Guidelines:
- Collect pet name and type (breed is also helpful).
- For medical emergencies or aggressive behavior, escalate to a human immediately.
- Mention current promotions (e.g., first-time grooming discount).
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" phone numbers** - If customer provides phone, accept it and move on.
""",
            "example_responses": {
                "booking": "I'd be happy to book that for your pet. What's your pet's name and what kind of service do you need?",
                "emergency": "If this is a medical emergency, please bring your pet in immediately or call our emergency line. I'll alert our staff.",
                "grooming": "We have openings for grooming this week. Does your pet have any special needs or sensitivities?",
            }
        },
        
        # ============================================================
        # BANKING - Restricted Autonomy (Financial)
        # ============================================================
        "banking": {
            "name": "Banking / Financial Institution",
            "icon": "account_balance",
            "autonomy_level": AutonomyLevel.RESTRICTED,
            "risk_profile": {
                "high_risk_intents": ["fraud_report", "suspicious_activity", "lost_card", "stolen_card", "unauthorized_transaction", "security_breach"],
                "auto_escalate_threshold": 0.4,
                "confidence_threshold": 0.8,
            },
            "common_intents": [
                "account_inquiry", "balance_inquiry", "transaction_inquiry", "loan_application",
                "mortgage_inquiry", "credit_card_application", "debit_card_issue", "atm_issue",
                "wire_transfer", "bill_payment", "branch_appointment", "investment_inquiry",
                "savings_account", "checking_account", "online_banking_help", "mobile_banking_issue"
            ],
            "fields": {
                "customer_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
                "account_number": {"required": False, "validation": "account_number", "prompt": "What's your account number? (Last 4 digits for verification)"},
                "service_type": {"required": True, "validation": "string", "prompt": "What banking service do you need?"},
                "preferred_date": {"required": False, "validation": "future_date", "prompt": "When would you like to visit the branch?"},
                "preferred_time": {"required": False, "validation": "string", "prompt": "What time works best?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "customer_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "service_type", "ask_if_missing": True},
                    {"field": "preferred_date", "ask_if_missing": False, "for_intents": ["branch_appointment", "loan_application"]},
                    {"field": "preferred_time", "ask_if_missing": False, "for_intents": ["branch_appointment", "loan_application"]},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Your {service_type} is confirmed for {preferred_date} at {preferred_time}. Please bring valid ID.",
            },
            "system_prompt_addition": """
## Banking-Specific Guidelines:
- CRITICAL SECURITY: Never ask for full account numbers, SSNs, PINs, or passwords over the phone.
- For fraud reports, lost/stolen cards, or suspicious activity - ESCALATE IMMEDIATELY to fraud department.
- For unauthorized transactions, guide customer to file a dispute form.
- Provide general account information only (no full account numbers or balances without verification).
- For loan/mortgage applications, collect basic info and schedule branch appointment.
- **DO NOT provide financial advice** - Only provide product information.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" info repeatedly** - If customer already confirmed, move on.
- For online/mobile banking issues, provide basic troubleshooting or schedule tech support.
""",
            "example_responses": {
                "account_inquiry": "I can help with your account. What would you like to know? (Note: I cannot provide full account numbers or detailed balances without proper verification)",
                "fraud_report": "For fraud reports or suspicious activity, I'm connecting you with our fraud department immediately. They'll help secure your account.",
                "branch_appointment": "I'd be happy to schedule an appointment at a branch. What service do you need and when would you like to visit?",
            }
        },

        # ============================================================
        # INSURANCE - Restricted Autonomy (Legal/Financial)
        # ============================================================
        "insurance": {
            "name": "Insurance Agency",
            "icon": "security",
            "autonomy_level": AutonomyLevel.RESTRICTED,
            "risk_profile": {
                "high_risk_intents": ["claim_dispute", "denied_claim", "coverage_denial", "legal_question", "fraud_report", "liability_issue"],
                "auto_escalate_threshold": 0.4,
                "confidence_threshold": 0.8,
            },
            "common_intents": [
                "file_claim", "policy_inquiry", "coverage_inquiry", "quote_request",
                "premium_inquiry", "payment_inquiry", "renewal_inquiry", "cancellation_inquiry",
                "policy_change", "add_coverage", "remove_coverage", "deductible_inquiry",
                "agent_appointment", "claim_status", "document_request", "proof_of_insurance"
            ],
            "fields": {
                "customer_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
                "policy_number": {"required": False, "validation": "policy_number", "prompt": "What's your policy number?"},
                "service_type": {"required": True, "validation": "string", "prompt": "What insurance service do you need?"},
                "claim_details": {"required": False, "validation": "string", "prompt": "Can you provide details about the incident?", "for_intents": ["file_claim"]},
                "preferred_date": {"required": False, "validation": "future_date", "prompt": "When would you like to meet with an agent?"},
                "preferred_time": {"required": False, "validation": "string", "prompt": "What time works best?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "customer_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "service_type", "ask_if_missing": True},
                    {"field": "policy_number", "ask_if_missing": False},
                    {"field": "claim_details", "ask_if_missing": False, "for_intents": ["file_claim"]},
                    {"field": "preferred_date", "ask_if_missing": False, "for_intents": ["agent_appointment"]},
                    {"field": "preferred_time", "ask_if_missing": False, "for_intents": ["agent_appointment"]},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Your {service_type} is confirmed for {preferred_date} at {preferred_time}. Please bring your policy documents.",
            },
            "system_prompt_addition": """
## Insurance-Specific Guidelines:
- CRITICAL COMPLIANCE: Never provide legal advice or interpret policy language that could be considered legal advice.
- For claim disputes, denied claims, or liability issues - ESCALATE to claims adjuster or agent.
- For filing claims, collect basic incident details and guide through the claims process.
- Provide general policy information and coverage details.
- For quotes, collect basic information and connect with an agent for personalized quotes.
- **DO NOT guarantee coverage** - Always advise customers to review their policy documents.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" info repeatedly** - If customer already confirmed, move on.
- For payment inquiries, provide account info or connect to billing department.
- For proof of insurance requests, provide general guidance on how to obtain documents.
""",
            "example_responses": {
                "file_claim": "I'm sorry to hear about your incident. Let me help you file a claim. What happened and when? (I'll collect basic details and connect you with our claims team)",
                "policy_inquiry": "I can help with your policy inquiry. What would you like to know about your coverage?",
                "claim_dispute": "For claim disputes or denied claims, I need to connect you with a claims adjuster who can review your case. Let me transfer you.",
            }
        },

        # ============================================================
        # VETERINARY - Restricted Autonomy (Healthcare)
        # ============================================================
        "veterinary": {
            "name": "Veterinary Clinic",
            "icon": "local_veterinarian",
            "autonomy_level": AutonomyLevel.RESTRICTED,
            "risk_profile": {
                "high_risk_intents": ["medical_emergency", "severe_symptoms", "poisoning", "trauma", "difficulty_breathing", "seizure", "unconscious"],
                "auto_escalate_threshold": 0.3,
                "confidence_threshold": 0.85,
            },
            "common_intents": [
                "book_appointment", "wellness_exam", "vaccination", "surgery_consultation",
                "symptoms_inquiry", "prescription_refill", "lab_results", "dental_care",
                "grooming_inquiry", "boarding_inquiry", "nutrition_consultation", "behavioral_consultation",
                "end_of_life_consultation", "microchip", "spay_neuter", "emergency_care"
            ],
            "fields": {
                "owner_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
                "pet_name": {"required": True, "validation": "string", "prompt": "What's your pet's name?"},
                "pet_type": {"required": True, "validation": "string", "prompt": "What type of pet is it? (dog, cat, etc.)"},
                "pet_breed": {"required": False, "validation": "string", "prompt": "What breed is your pet?"},
                "pet_age": {"required": False, "validation": "string", "prompt": "How old is your pet?"},
                "service_type": {"required": True, "validation": "string", "prompt": "What veterinary service do you need?"},
                "symptoms": {"required": False, "validation": "string", "prompt": "Can you describe your pet's symptoms?", "for_intents": ["symptoms_inquiry", "emergency_care"]},
                "preferred_date": {"required": True, "validation": "future_date", "prompt": "What date works for the appointment?"},
                "preferred_time": {"required": True, "validation": "string", "prompt": "What time works best?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "owner_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "pet_name", "ask_if_missing": True},
                    {"field": "pet_type", "ask_if_missing": True},
                    {"field": "pet_breed", "ask_if_missing": False},
                    {"field": "pet_age", "ask_if_missing": False},
                    {"field": "service_type", "ask_if_missing": True},
                    {"field": "symptoms", "ask_if_missing": False, "for_intents": ["symptoms_inquiry", "emergency_care"]},
                    {"field": "preferred_date", "ask_if_missing": True},
                    {"field": "preferred_time", "ask_if_missing": True},
                ],
                "final_action": "CREATE_APPOINTMENT",
                "confirmation_message": "Your appointment for {pet_name} ({pet_type}) for {service_type} is confirmed for {preferred_date} at {preferred_time}. Please bring vaccination records.",
            },
            "system_prompt_addition": """
## Veterinary Clinic-Specific Guidelines:
- CRITICAL SAFETY: For medical emergencies (difficulty breathing, seizures, trauma, poisoning, unconscious) - ADVISE IMMEDIATE TRANSPORT TO CLINIC and ESCALATE to veterinary team.
- **DO NOT provide medical diagnosis or treatment advice** - Only schedule appointments and provide general information.
- For wellness exams and vaccinations, schedule routine appointments.
- For prescription refills, advise that veterinarian approval is required.
- Maintain confidentiality of all pet health information.
- For severe symptoms, prioritize and offer same-day appointments if available.
- **DO NOT repeat questions** - Track collected information.
- **DO NOT ask to "confirm" phone numbers** - If owner provides phone, accept it and move on.
- **DO NOT ask to "verify" information** - Trust what the owner tells you.
- For end-of-life consultations, handle with empathy and connect with veterinarian.
""",
            "example_responses": {
                "book_appointment": "I'd be happy to schedule an appointment for your pet. What's your pet's name and what service do you need?",
                "emergency_care": "This sounds like an emergency. Please bring your pet to the clinic immediately - we have veterinarians on call. I'm alerting our team now.",
                "wellness_exam": "I can schedule a wellness exam for {pet_name}. What date and time works best for you?",
                "symptoms_inquiry": "I'm concerned to hear about {pet_name}'s symptoms. Can you describe what's happening so I can determine the urgency?",
            }
        },

        # ============================================================
        # GENERAL BUSINESS - Default
        # ============================================================
        "general": {
            "name": "General Business",
            "icon": "business",
            "autonomy_level": AutonomyLevel.MEDIUM,
            "risk_profile": {
                "high_risk_intents": ["legal_question", "safety_concern"],
                "auto_escalate_threshold": 0.5,
                "confidence_threshold": 0.6,
            },
            "common_intents": [
                "general_inquiry", "hours_inquiry", "location_inquiry",
                "contact_info", "appointment_booking", "callback_request"
            ],
            "fields": {
                "customer_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
                "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
                "reason": {"required": False, "validation": "string", "prompt": "How can I help you today?"},
            },
            "booking_flow": {
                "type": "appointment",
                "steps": [
                    {"field": "customer_name", "ask_if_missing": True},
                    {"field": "phone", "ask_if_missing": True},
                    {"field": "reason", "ask_if_missing": False},
                ],
                "final_action": "CREATE_APPOINTMENT",
            },
            "system_prompt_addition": """
## General Business Guidelines:
- Be polite and professional.
- Collect caller information.
- **DO NOT repeat questions** - Track collected information.
""",
            "example_responses": {
                "greeting": "Thank you for calling. How may I assist you today?",
                "callback": "Would you like us to call you back?",
            }
        }
    }
    
    @classmethod
    def get_template(cls, business_type: str, db=None) -> Dict[str, Any]:
        """
        Get template for a business type.
        
        Prioritizes database templates if available and db session is provided.
        Falls back to hardcoded templates as backup.
        """
        # Try database first if integration is available
        if DB_INTEGRATION_AVAILABLE and db is not None:
            try:
                return get_template(business_type, db)
            except Exception:
                # Fall back to hardcoded templates on error
                pass
        
        # Fall back to hardcoded templates
        return cls.TEMPLATES.get(business_type, cls.TEMPLATES["general"])
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get list of all available business types"""
        return list(cls.TEMPLATES.keys())
    
    @classmethod
    def get_template_prompt(cls, business_type: str) -> str:
        """Get the system prompt addition for a business type"""
        template = cls.get_template(business_type)
        return template.get("system_prompt_addition", "")
    
    @classmethod
    def get_required_info(cls, business_type: str) -> List[str]:
        """Get required information fields for a business type"""
        template = cls.get_template(business_type)
        fields = template.get("fields", {})
        return [name for name, config in fields.items() if config.get("required", False)]
    
    @classmethod
    def get_example_response(cls, business_type: str, intent: str) -> str:
        """Get example response for a business type and intent"""
        template = cls.get_template(business_type)
        examples = template.get("example_responses", {})
        return examples.get(intent, "")
    
    @classmethod
    def get_booking_flow(cls, business_type: str) -> Dict[str, Any]:
        """Get the booking flow configuration for a business type"""
        template = cls.get_template(business_type)
        return template.get("booking_flow", {})
    
    @classmethod
    def get_risk_profile(cls, business_type: str) -> Dict[str, Any]:
        """Get the risk profile for a business type"""
        template = cls.get_template(business_type)
        return template.get("risk_profile", {
            "high_risk_intents": [],
            "auto_escalate_threshold": 0.5,
            "confidence_threshold": 0.6,
        })
    
    @classmethod
    def get_autonomy_level(cls, business_type: str) -> str:
        """Get the autonomy level for a business type"""
        template = cls.get_template(business_type)
        return template.get("autonomy_level", AutonomyLevel.MEDIUM)
    
    @classmethod
    def get_fields(cls, business_type: str) -> Dict[str, Dict[str, Any]]:
        """Get all fields with their configuration for a business type"""
        template = cls.get_template(business_type)
        return template.get("fields", {})
    
    @classmethod
    def get_next_missing_field(cls, business_type: str, collected: Dict[str, str], intent: str = None) -> Optional[Dict[str, Any]]:
        """
        Determine the next field to ask for based on booking flow configuration.
        This now supports both field-based and intent-based steps.
        """
        template = cls.get_template(business_type)
        
        # Determine which flow to use (e.g., order_food_flow, reservation_flow)
        flow = {}
        if intent == "order_food" and "order_food_flow" in template:
            flow = template["order_food_flow"]
        elif intent == "make_reservation" and "reservation_flow" in template:
            flow = template["reservation_flow"]
        else:
            flow = template.get("booking_flow", {})

        steps = flow.get("steps", [])
        fields = template.get("fields", {})
        
        for step in steps:
            if "field" in step:
                field_name = step["field"]
                ask_if_missing = step.get("ask_if_missing", True)
                for_intents = step.get("for_intents")

                if not ask_if_missing or (for_intents and intent not in for_intents):
                    continue
                
                if field_name not in collected or not collected[field_name]:
                    field_config = fields.get(field_name, {})
                    return {
                        "type": "field",
                        "field": field_name,
                        "prompt": field_config.get("prompt", f"Please provide {field_name}"),
                        "validation": field_config.get("validation", "string"),
                    }
            elif "intent" in step:
                # This is a conversational goal, not a data field
                step_intent = step["intent"]
                # Check if this conversational step has already been "satisfied"
                if f"satisfied_{step_intent}" not in collected:
                    return {
                        "type": "intent",
                        "intent": step_intent,
                        "prompt": step.get("prompt", f"I was wondering about {step_intent}"),
                    }
        
        return None  # All steps completed
    
    @classmethod
    def validate_field(cls, field_name: str, value: str, validation_type: str) -> bool:
        """Validate a field value using the specified validation type"""
        validator = cls.VALIDATORS.get(validation_type, FieldValidation.validate_string)
        return validator(value)
    
    @classmethod
    def get_governance_tier(
        cls, 
        business_type: str, 
        intent: str, 
        confidence: float,
        action: str = None,
        entities: Dict[str, Any] = None
    ) -> GovernanceTier:
        """
        Determine governance tier based on multi-factor analysis.
        
        This is a 3-layer governance engine that incorporates:
        - Autonomy level of the business type
        - Risk profile and high-risk intents
        - Model confidence
        - Action risk classification
        - Intent-specific handling
        
        Args:
            business_type: Type of business (restaurant, medical, etc.)
            intent: Current detected intent
            confidence: Model confidence score (0-1)
            action: The action being considered (optional)
            entities: Extracted entities (optional, for context)
            
        Returns:
            GovernanceTier indicating how to handle the action
        """
        template = cls.get_template(business_type)
        risk_profile = cls.get_risk_profile(business_type)
        autonomy_level = template.get("autonomy_level", AutonomyLevel.MEDIUM)
        
        high_risk_intents = risk_profile.get("high_risk_intents", [])
        auto_escalate_threshold = risk_profile.get("auto_escalate_threshold", 0.5)
        confidence_threshold = risk_profile.get("confidence_threshold", 0.6)
        
        # Action risk mapping
        action_risk_map = {
            # Critical actions - always need oversight for RESTRICTED
            "HUMAN_INTERVENTION": ActionRisk.CRITICAL,
            "TRANSFER_HUMAN": ActionRisk.CRITICAL,
            
            # High risk actions
            "PAYMENT_PROCESS": ActionRisk.HIGH,
            "HANDLE_COMPLAINT": ActionRisk.HIGH,
            "UPDATE_CRM": ActionRisk.HIGH,
            
            # Medium risk actions
            "CREATE_APPOINTMENT": ActionRisk.MEDIUM,
            "CREATE_ORDER": ActionRisk.MEDIUM,
            "CONFIRM_ORDER": ActionRisk.MEDIUM,
            "PLACE_ORDER": ActionRisk.MEDIUM,
            "RESCHEDULE_APPOINTMENT": ActionRisk.MEDIUM,
            "CANCEL_APPOINTMENT": ActionRisk.MEDIUM,
            
            # Low risk actions
            "PROVIDE_INFO": ActionRisk.LOW,
            "SEND_DIRECTIONS": ActionRisk.LOW,
            "COLLECT_INFO": ActionRisk.LOW,
            "TAKE_MESSAGE": ActionRisk.LOW,
        }
        
        action_risk = action_risk_map.get(action, ActionRisk.MEDIUM)
        
        # ===== GOVERNANCE TIER DETERMINATION =====
        
        # Layer 1: Critical intent detection (highest priority)
        # These are situations that ALWAYS require human involvement
        critical_intent_patterns = [
            "emergency", "safety", "gas_leak", "carbon_monoxide",
            "arrest", "court_date", "medical_emergency", "severe_pain"
        ]
        intent_lower = intent.lower() if intent else ""
        if any(pattern in intent_lower for pattern in critical_intent_patterns):
            return GovernanceTier.PRIORITY_FLOW  # Provide safety instructions, then escalate
        
        # Layer 2: High-risk intent from profile
        if intent in high_risk_intents:
            if autonomy_level == AutonomyLevel.RESTRICTED:
                return GovernanceTier.HUMAN_REVIEW
            elif autonomy_level == AutonomyLevel.MEDIUM:
                return GovernanceTier.PRIORITY_FLOW
            else:
                return GovernanceTier.CONFIRM_BEFORE_EXECUTE
        
        # Layer 3: Confidence-based governance
        if confidence < auto_escalate_threshold:
            return GovernanceTier.ESCALATE_IMMEDIATE
        
        # Layer 4: Autonomy-level-based action governance
        if autonomy_level == AutonomyLevel.RESTRICTED:
            # RESTRICTED: All medium+ risk actions need confirmation
            if action_risk in [ActionRisk.HIGH, ActionRisk.CRITICAL]:
                return GovernanceTier.HUMAN_REVIEW
            elif action_risk == ActionRisk.MEDIUM:
                return GovernanceTier.CONFIRM_BEFORE_EXECUTE
            # Low risk can auto-execute
            
        elif autonomy_level == AutonomyLevel.MEDIUM:
            # MEDIUM: High risk needs confirmation, critical escalates
            if action_risk == ActionRisk.CRITICAL:
                return GovernanceTier.ESCALATE_IMMEDIATE
            elif action_risk == ActionRisk.HIGH:
                return GovernanceTier.CONFIRM_BEFORE_EXECUTE
            # Medium and low risk can auto-execute
            
        else:  # HIGH autonomy
            # HIGH: Only critical actions escalate, everything else auto
            if action_risk == ActionRisk.CRITICAL:
                return GovernanceTier.PRIORITY_FLOW
            # All else auto-executes
        
        # Layer 5: Confidence threshold check
        if confidence < confidence_threshold:
            return GovernanceTier.CONFIRM_BEFORE_EXECUTE
        
        # Default: Auto-execute
        return GovernanceTier.AUTO
    
    @classmethod
    def should_escalate(cls, business_type: str, intent: str, confidence: float) -> bool:
        """
        Backward-compatible wrapper around get_governance_tier.
        Returns True if governance tier requires human involvement.
        """
        tier = cls.get_governance_tier(business_type, intent, confidence)
        return tier in [
            GovernanceTier.PRIORITY_FLOW,
            GovernanceTier.HUMAN_REVIEW,
            GovernanceTier.ESCALATE_IMMEDIATE
        ]
    
    @classmethod
    def get_execution_policy(cls, governance_tier: GovernanceTier) -> Dict[str, Any]:
        """
        Get execution policy for a governance tier.
        
        Returns:
            Dictionary with execution instructions
        """
        policies = {
            GovernanceTier.AUTO: {
                "requires_confirmation": False,
                "requires_human_approval": False,
                "provide_safety_instructions": False,
                "log_level": "info",
                "description": "Execute automatically without oversight"
            },
            GovernanceTier.CONFIRM_BEFORE_EXECUTE: {
                "requires_confirmation": True,
                "requires_human_approval": False,
                "provide_safety_instructions": False,
                "log_level": "warning",
                "description": "Ask user to confirm before executing"
            },
            GovernanceTier.PRIORITY_FLOW: {
                "requires_confirmation": False,
                "requires_human_approval": True,
                "provide_safety_instructions": True,
                "log_level": "error",
                "description": "Execute with safety instructions, then escalate to human"
            },
            GovernanceTier.HUMAN_REVIEW: {
                "requires_confirmation": False,
                "requires_human_approval": True,
                "provide_safety_instructions": False,
                "log_level": "error",
                "description": "Pause for human approval before any action"
            },
            GovernanceTier.ESCALATE_IMMEDIATE: {
                "requires_confirmation": False,
                "requires_human_approval": True,
                "provide_safety_instructions": True,
                "log_level": "critical",
                "description": "Immediate transfer to human, AI provides initial response"
            }
        }
        return policies.get(governance_tier, policies[GovernanceTier.AUTO])
    
    @classmethod
    def build_confirmation_message(
        cls,
        business_type: str,
        collected_data: Dict[str, str],
        action: str = None,
        include_missing_fields: bool = False
    ) -> Dict[str, Any]:
        """
        Build a dynamic confirmation message with validation.
        
        Args:
            business_type: Type of business
            collected_data: Dictionary of collected field values
            action: The action being confirmed (optional)
            include_missing_fields: Whether to note missing required fields
            
        Returns:
            Dictionary with confirmation message, validated data, and any issues
        """
        template = cls.get_template(business_type)
        booking_flow = template.get("booking_flow", {})
        fields = template.get("fields", {})
        
        # Get the confirmation template
        confirmation_template = booking_flow.get("confirmation_message", 
            "Your request has been confirmed.")
        
        # Validate all collected data
        validated_data = {}
        validation_issues = []
        
        for field_name, value in collected_data.items():
            field_config = fields.get(field_name, {})
            validation_type = field_config.get("validation", "string")
            
            if value:
                is_valid = cls.validate_field(field_name, str(value), validation_type)
                if is_valid:
                    validated_data[field_name] = value
                else:
                    validation_issues.append({
                        "field": field_name,
                        "value": value,
                        "issue": f"Invalid format for {field_name}"
                    })
        
        # Build confirmation message by replacing placeholders
        message = confirmation_template
        for field_name, value in validated_data.items():
            placeholder = "{" + field_name + "}"
            if placeholder in message:
                message = message.replace(placeholder, str(value))
        
        # Handle missing placeholders (remove them or use defaults)
        import re
        remaining_placeholders = re.findall(r'\{(\w+)\}', message)
        for placeholder in remaining_placeholders:
            if placeholder in validated_data:
                continue
            # Check if there's a default value in the flow
            flow_steps = booking_flow.get("steps", [])
            default_value = None
            for step in flow_steps:
                if step.get("field") == placeholder:
                    default_value = step.get("default")
                    break
            if default_value:
                message = message.replace("{" + placeholder + "}", str(default_value))
            else:
                # Remove the placeholder if no value available
                message = message.replace("{" + placeholder + "}", "[pending]")
        
        # Check for missing required fields
        missing_required = []
        if include_missing_fields:
            for field_name, config in fields.items():
                if config.get("required") and field_name not in validated_data:
                    missing_required.append({
                        "field": field_name,
                        "prompt": config.get("prompt", f"Please provide {field_name}")
                    })
        
        return {
            "message": message,
            "validated_data": validated_data,
            "validation_issues": validation_issues,
            "missing_required": missing_required,
            "all_fields_valid": len(validation_issues) == 0 and len(missing_required) == 0
        }
    
    @classmethod
    def create_audit_record(
        cls,
        business_type: str,
        session_id: str,
        intent: str,
        action: str,
        governance_tier: GovernanceTier,
        confidence: float,
        entities: Dict[str, Any],
        collected_data: Dict[str, str],
        executed: bool = False,
        human_approved: bool = None
    ) -> Dict[str, Any]:
        """
        Create a structured audit log record for compliance and debugging.
        
        Args:
            business_type: Type of business
            session_id: Call/conversation session ID
            intent: Detected intent
            action: Action taken or proposed
            governance_tier: Governance tier applied
            confidence: Model confidence score
            entities: Extracted entities
            collected_data: Collected field data
            executed: Whether action was executed
            human_approved: Whether human approved (if applicable)
            
        Returns:
            Audit record dictionary
        """
        from datetime import datetime, timezone
        
        template = cls.get_template(business_type)
        autonomy_level = template.get("autonomy_level", AutonomyLevel.MEDIUM)
        risk_profile = cls.get_risk_profile(business_type)
        execution_policy = cls.get_execution_policy(governance_tier)
        
        return {
            "audit_id": f"{session_id}_{datetime.now(timezone.utc).isoformat()}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "business_context": {
                "type": business_type,
                "autonomy_level": autonomy_level,
                "risk_profile": risk_profile,
            },
            "decision": {
                "intent": intent,
                "action": action,
                "governance_tier": governance_tier,
                "confidence": confidence,
                "requires_confirmation": execution_policy.get("requires_confirmation", False),
                "requires_human_approval": execution_policy.get("requires_human_approval", False),
            },
            "data": {
                "entities": entities,
                "collected": collected_data,
            },
            "outcome": {
                "executed": executed,
                "human_approved": human_approved,
            },
            "log_level": execution_policy.get("log_level", "info"),
        }
    
    @classmethod
    def get_flow_prompt_context(cls, business_type: str) -> str:
        """
        Generate a concise prompt context for Nova based on structured flow config.
        This replaces verbose prompt instructions with data-driven guidance.
        """
        template = cls.get_template(business_type)
        fields = template.get("fields", {})
        booking_flow = template.get("booking_flow", {})
        risk_profile = cls.get_risk_profile(business_type)
        autonomy_level = template.get("autonomy_level", AutonomyLevel.MEDIUM)
        
        required_fields = [name for name, config in fields.items() if config.get("required")]
        
        context = f"""
## Business Configuration:
- Autonomy Level: {autonomy_level}
- Required Fields: {', '.join(required_fields)}
- High-Risk Intents (auto-escalate): {', '.join(risk_profile.get('high_risk_intents', []))}
- Confidence Threshold: {risk_profile.get('confidence_threshold', 0.6)}
- Final Action: {booking_flow.get('final_action', 'CREATE_APPOINTMENT')}

## Field Collection Order:
{chr(10).join([f"{i+1}. {step.get('field')}" for i, step in enumerate(booking_flow.get('steps', []))])}

## Anti-Repetition Rules:
- Track collected fields internally
- Only ask for missing fields
- DO NOT repeat information already provided
"""
        return context
    
    @classmethod
    def calculate_dynamic_risk_score(
        cls,
        business_type: str,
        intent: str,
        confidence: float,
        action: str,
        entities: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None,
        real_time_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Calculate dynamic risk score based on multiple factors
        
        Args:
            business_type: Type of business
            intent: Detected intent
            confidence: Model confidence score
            action: Selected action
            entities: Extracted entities
            conversation_history: Recent conversation history
            real_time_context: Real-time context (sentiment, urgency, etc.)
            
        Returns:
            Dictionary with risk score and contributing factors
        """
        risk_profile = cls.get_risk_profile(business_type)
        high_risk_intents = risk_profile.get("high_risk_intents", [])
        
        # Base risk from intent
        base_risk = 0.3  # Default baseline risk
        
        # Intent risk factor
        if intent in high_risk_intents:
            base_risk += 0.4
        
        # Confidence risk factor (lower confidence = higher risk)
        if confidence < 0.5:
            base_risk += 0.3
        elif confidence < 0.7:
            base_risk += 0.15
        
        # Action risk factor
        high_risk_actions = ["HUMAN_INTERVENTION", "PAYMENT_PROCESS", "HANDLE_COMPLAINT"]
        if action in high_risk_actions:
            base_risk += 0.2
        
        # Conversation history analysis
        history_risk = 0.0
        if conversation_history:
            recent_messages = conversation_history[-5:]  # Last 5 messages
            
            # Check for escalation patterns
            escalation_keywords = ["manager", "supervisor", "complaint", "unhappy", "angry"]
            escalation_count = sum(
                1 for msg in recent_messages
                if any(keyword in msg.get("content", "").lower() for keyword in escalation_keywords)
            )
            history_risk += escalation_count * 0.1
            
            # Check for repeated issues
            if len(conversation_history) > 10:
                history_risk += 0.1
        
        # Real-time context factors
        context_risk = 0.0
        if real_time_context:
            # Sentiment factor
            sentiment = real_time_context.get("sentiment", "neutral")
            if sentiment == "negative":
                context_risk += 0.2
            elif sentiment == "angry":
                context_risk += 0.4
            
            # Urgency factor
            urgency = real_time_context.get("urgency", "low")
            if urgency == "high":
                context_risk += 0.15
            elif urgency == "critical":
                context_risk += 0.3
            
            # Customer value factor
            is_vip = real_time_context.get("is_vip", False)
            if is_vip:
                context_risk += 0.1  # Slightly higher risk for VIPs to ensure quality
        
        # Combine all risk factors with weights
        total_risk = (
            base_risk * 0.4 +
            history_risk * 0.3 +
            context_risk * 0.3
        )
        
        # Cap at 1.0
        total_risk = min(total_risk, 1.0)
        
        # Determine risk level
        if total_risk >= 0.7:
            risk_level = "critical"
        elif total_risk >= 0.5:
            risk_level = "high"
        elif total_risk >= 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": round(total_risk, 2),
            "risk_level": risk_level,
            "factors": {
                "intent_risk": 0.4 if intent in high_risk_intents else 0.0,
                "confidence_risk": 0.3 if confidence < 0.5 else 0.0,
                "action_risk": 0.2 if action in high_risk_actions else 0.0,
                "history_risk": round(history_risk, 2),
                "context_risk": round(context_risk, 2)
            },
            "thresholds": {
                "governance_threshold": risk_profile.get("auto_escalate_threshold", 0.5),
                "confidence_threshold": risk_profile.get("confidence_threshold", 0.6)
            }
        }
    
    @classmethod
    def detect_bias(cls, conversation: str, entities: Dict[str, Any], db=None) -> Dict[str, Any]:
        """
        Detect potential biases in conversation and decision-making
        
        Args:
            conversation: Conversation text to analyze
            entities: Extracted entities
            db: Database session for historical analysis
            
        Returns:
            Dictionary with bias detection results
        """
        import re
        
        # Define bias indicators
        bias_indicators = {
            "age_bias": ["young", "old", "elderly", "teenager", "senior"],
            "gender_bias": ["he", "she", "him", "her", "male", "female", "man", "woman"],
            "racial_bias": ["ethnicity", "race", "nationality", "accent"],
            "socioeconomic_bias": ["wealthy", "poor", "rich", "expensive", "cheap"]
        }
        
        detected_biases = []
        bias_evidence = {}
        
        # Analyze conversation for bias indicators
        conversation_lower = conversation.lower()
        
        for bias_type, keywords in bias_indicators.items():
            found_keywords = [kw for kw in keywords if kw in conversation_lower]
            if found_keywords:
                detected_biases.append(bias_type)
                bias_evidence[bias_type] = {
                    "keywords": found_keywords,
                    "context": cls._extract_bias_context(conversation, found_keywords)
                }
        
        # Analyze entity-based bias
        entity_bias_risk = 0.0
        if entities:
            # Check for demographic-based entity selection
            demographic_fields = ["age", "gender", "ethnicity", "income_level"]
            has_demographic_fields = any(field in entities for field in demographic_fields)
            
            if has_demographic_fields:
                entity_bias_risk = 0.3
                detected_biases.append("demographic_entity_usage")
        
        # Check for bias in treatment patterns (if historical data available)
        historical_bias = cls._analyze_historical_bias(entities, db) if db else {}
        
        # Calculate overall bias risk score
        bias_count = len(detected_biases)
        overall_bias_risk = min(0.1 + (bias_count * 0.2) + entity_bias_risk, 1.0)
        
        # Determine bias level
        if overall_bias_risk >= 0.6:
            bias_level = "high"
        elif overall_bias_risk >= 0.3:
            bias_level = "medium"
        elif overall_bias_risk > 0:
            bias_level = "low"
        else:
            bias_level = "none"
        
        return {
            "bias_detected": len(detected_biases) > 0,
            "bias_level": bias_level,
            "bias_score": round(overall_bias_risk, 2),
            "detected_biases": detected_biases,
            "evidence": bias_evidence,
            "historical_analysis": historical_bias,
            "recommendations": cls._get_bias_mitigation_recommendations(detected_biases, bias_level)
        }
    
    @classmethod
    def _extract_bias_context(cls, conversation: str, keywords: List[str]) -> str:
        """Extract context around bias keywords."""
        import re
        
        context = []
        for keyword in keywords:
            # Find keyword and surrounding text
            pattern = rf'.{{0,50}}{re.escape(keyword)}.{{0,50}}'
            matches = re.findall(pattern, conversation, re.IGNORECASE)
            if matches:
                context.extend(matches)
        
        return " ... ".join(context[:3])  # Limit to 3 contexts
    
    @classmethod
    def _analyze_historical_bias(cls, entities: Dict[str, Any], db) -> Dict[str, Any]:
        """Analyze historical data for bias patterns."""
        # This would query historical data to identify patterns
        # For now, return empty dict as placeholder
        return {
            "analyzed": False,
            "reason": "Historical bias analysis not implemented"
        }
    
    @classmethod
    def _get_bias_mitigation_recommendations(cls, detected_biases: List[str], bias_level: str) -> List[str]:
        """Get recommendations for mitigating detected biases."""
        recommendations = []
        
        if bias_level == "none":
            return ["No bias detected - continue current practices"]
        
        recommendations.append("Review and adjust response to ensure equitable treatment")
        
        if "age_bias" in detected_biases:
            recommendations.append("Remove age-related references or assumptions")
        
        if "gender_bias" in detected_biases:
            recommendations.append("Use gender-neutral language and avoid gender-based assumptions")
        
        if "racial_bias" in detected_biases:
            recommendations.append("Remove references to ethnicity, race, or nationality unless relevant")
        
        if "socioeconomic_bias" in detected_biases:
            recommendations.append("Avoid assumptions based on perceived wealth or income level")
        
        if bias_level == "high":
            recommendations.append("Consider human review before proceeding")
            recommendations.append("Document the situation for bias monitoring")
        
        return recommendations