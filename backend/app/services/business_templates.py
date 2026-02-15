"""
Business Type Templates - Pre-built AI behaviors for different business types
"""

from typing import Dict, Any, List

class BusinessTypeTemplate:
    """Template for different business types"""
    
    # Pre-defined business types with their characteristics
    TEMPLATES: Dict[str, Dict[str, Any]] = {
        "restaurant": {
            "name": "Restaurant",
            "icon": "restaurant",
            "common_intents": [
                "make_reservation", "order_food", "menu_inquiry", 
                "dietary_options", "hours_inquiry", "location_inquiry",
                "special_events", "catering", "wait_time", "pricing_inquiry"
            ],
            "required_info": ["party_size", "date", "time"],
            "system_prompt_addition": """
## Restaurant-Specific Guidelines:
- CRITICAL - PRICING: When customers ask about prices, provide EXACT price from Menu. When ordering multiple items, ALWAYS calculate and provide the TOTAL price.
- When customer orders multiple items, calculate: item1 price + item2 price = TOTAL. Say "Your total is $XX.XX"
- After customer confirms items, THEN ask for name and phone for delivery/pickup
- When customer says yes to ordering, confirm the items and total first, THEN collect contact info
- Do NOT repeat the price multiple times in one response
- Handle to-go orders and delivery inquiries
- Be familiar with menu items, prices, and ingredients
""",
            "example_responses": {
                "reservation": "I'd be happy to help you reserve a table. How many guests will be joining?",
                "order": "Great choice! Would you like that for here or to go?",
                "pricing": "Our fried rice is $12.99. Would you like to order that?",
                "menu": "We have a variety of options including appetizers, main courses, and desserts. What type of cuisine are you interested in?"
            }
        },
        
        "hotel": {
            "name": "Hotel",
            "icon": "hotel",
            "common_intents": [
                "book_room", "check_availability", "amenities_inquiry",
                "check_in_out", "room_service", "pool_gym", "wifi_password",
                "late_checkout", "early_checkin", "parking", "pet_policy",
                "conference_rooms", " airport_shuttle", "breakfast_included"
            ],
            "required_info": ["check_in_date", "check_out_date", "room_type", "number_of_guests"],
            "system_prompt_addition": """
## Hotel-Specific Guidelines:
- Know room types and current rates
- Handle booking modifications and cancellations
- Provide information about amenities (pool, gym, spa, restaurant)
- Assist with check-in/check-out processes
- Handle room service orders
- Know policy on late checkout, early check-in
- Answer questions about parking, WiFi, pet policies
- Handle corporate account and group bookings
""",
            "example_responses": {
                "booking": "I'd be happy to help you book a room. What dates are you looking at?",
                "amenities": "Our hotel features a fitness center, outdoor pool, on-site restaurant, and free WiFi throughout the property.",
                "checkout": "Standard checkout is at 11 AM. We can arrange late checkout based on availability."
            }
        },
        
        "dental": {
            "name": "Dental Clinic",
            "icon": "medical_services",
            "common_intents": [
                "book_appointment", "emergency_dental", "checkup_cleaning",
                "cosmetic_dentistry", "insurance_inquiry", "new_patient",
                "tooth_pain", "whitening", "cavity", "root_canal"
            ],
            "required_info": ["patient_name", "phone", "preferred_date", "service_type"],
            "system_prompt_addition": """
## Dental Clinic-Specific Guidelines:
- Collect patient name and contact information
- Ask about insurance provider and coverage
- Inquire about the nature of the dental issue
- Know available appointment slots
- Handle dental emergencies with priority
- Understand different services: cleaning, checkup, whitening, extraction, etc.
- New patient paperwork and first visit procedures
""",
            "example_responses": {
                "appointment": "I'll schedule you for a checkup. What date and time works best for you?",
                "emergency": "We have same-day emergency appointments available. Can you describe your symptoms?",
                "insurance": "We accept most major insurance plans. Let me verify your coverage."
            }
        },
        
        "medical": {
            "name": "Medical Clinic",
            "icon": "local_hospital",
            "common_intents": [
                "book_appointment", "symptoms_inquiry", "prescription_refill",
                "lab_results", "insurance_inquiry", "new_patient",
                "urgent_care", "telehealth", "vaccinations", "specialist_referral"
            ],
            "required_info": ["patient_name", "phone", "date", "reason_for_visit"],
            "system_prompt_addition": """
## Medical Clinic-Specific Guidelines:
- Follow HIPAA compliance in handling patient information
- Collect insurance information and verify coverage
- Triage symptoms to determine urgency
- Handle prescription refill requests
- Schedule appointments with appropriate providers
- Know which services are offered at the clinic
- Handle telehealth appointment scheduling
""",
            "example_responses": {
                "appointment": "I can schedule you with one of our providers. What type of visit do you need?",
                "symptoms": "I'd like to help you schedule an appointment. Can you briefly describe your symptoms?",
                "prescription": "For prescription refills, please allow 24-48 hours. Which pharmacy would you prefer?"
            }
        },
        
        "law_firm": {
            "name": "Law Firm",
            "icon": "gavel",
            "common_intents": [
                "consultation_request", "case_evaluation", "legal_advice",
                "family_law", "criminal_defense", "real_estate", "business_law",
                "immigration", "personal_injury", "divorce", "contract_review"
            ],
            "required_info": ["client_name", "phone", "brief_case_description", "legal_matter_type"],
            "system_prompt_addition": """
## Law Firm-Specific Guidelines:
- Determine the area of law needed (family, criminal, business, etc.)
- Collect basic case information for attorney matching
- Schedule initial consultations
- Explain attorney-client privilege
- Know billing structure (hourly, flat fee, contingency)
- Handle urgent legal matters with priority
- Maintain confidentiality in all communications
""",
            "example_responses": {
                "consultation": "I'd be happy to schedule a consultation. Could you briefly describe your legal matter?",
                "areas": "Our firm handles family law, criminal defense, business law, personal injury, and more.",
                "fees": "Our consultation is $X. We'll discuss the fee structure based on your case details."
            }
        },
        
        "salon": {
            "name": "Salon / Spa",
            "icon": "content_cut",
            "common_intents": [
                "book_appointment", "haircut", "coloring", "styling",
                "nails", "massage", "facial", "spa_package",
                "products_inquiry", "stylist_preference", "bride_package"
            ],
            "required_info": ["customer_name", "phone", "service_type", "preferred_date"],
            "system_prompt_addition": """
## Salon/Spa-Specific Guidelines:
- Know all services and their durations/pricing
- Handle stylist/therapist preferences
- Book appointments based on service duration
- Know product lines for retail inquiries
- Handle special occasion packages (bridal, prom)
- Manage cancellation policies
- Suggest complementary services
""",
            "example_responses": {
                "booking": "What service are you looking for? We have appointments available on...",
                "stylist": "Do you have a stylist preference? Otherwise, we can assign someone available.",
                "products": "Yes, we carry professional products. Would you like recommendations?"
            }
        },
        
        "retail": {
            "name": "Retail Store",
            "icon": "shopping_bag",
            "common_intents": [
                "product_inquiry", "price_check", "store_hours",
                "return_policy", "loyalty_program", "gift_cards",
                "inventory_check", "online_order", "store_location"
            ],
            "required_info": ["product_name", "quantity"],
            "system_prompt_addition": """
## Retail Store-Specific Guidelines:
- Know product inventory and pricing
- Handle returns and exchanges per policy
- Explain loyalty program benefits
- Process gift card inquiries and purchases
- Handle online order pickups
- Know current promotions and sales
- Direct to appropriate department if needed
""",
            "example_responses": {
                "product": "Let me check our inventory for that item.",
                "returns": "Our return policy is 30 days with receipt. Do you have the receipt?",
                "loyalty": "Our loyalty program offers points for every purchase and exclusive member discounts!"
            }
        },
        
        "auto_repair": {
            "name": "Auto Repair",
            "icon": "directions_car",
            "common_intents": [
                "schedule_service", "oil_change", "tire_rotation",
                "brake_service", "engine_check", "diagnostics",
                "appointment_status", "warranty_inquiry", "cost_estimate"
            ],
            "required_info": ["vehicle_info", "service_type", "preferred_date", "contact_info"],
            "system_prompt_addition": """
## Auto Repair-Specific Guidelines:
- Collect vehicle information (make, model, year, mileage)
- Determine the type of service needed
- Provide cost estimates when possible
- Explain warranty coverage
- Schedule appointments based on service duration
- Handle towing and rental car inquiries
- Update on repair status
""",
            "example_responses": {
                "service": "What type of service does your vehicle need?",
                "estimate": "I can provide an estimate once our technicians examine the vehicle.",
                "appointment": "When would you like to bring your car in?"
            }
        },
        
        "general": {
            "name": "General Business",
            "icon": "business",
            "common_intents": [
                "general_inquiry", "hours_inquiry", "location_inquiry",
                "contact_info", "appointment_booking", "callback_request"
            ],
            "required_info": ["customer_name", "phone", "reason"],
            "system_prompt_addition": """
## General Business Guidelines:
- Be polite and professional
- Collect caller information
- Determine the purpose of the call
- Direct to appropriate department or take message
- Offer to schedule callbacks
""",
            "example_responses": {
                "greeting": "Thank you for calling. How may I assist you today?",
                "transfer": "Let me transfer you to the appropriate department.",
                "callback": "Would you like us to call you back?"
            }
        }
    }
    
    @classmethod
    def get_template(cls, business_type: str) -> Dict[str, Any]:
        """Get template for a business type"""
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
        return template.get("required_info", [])
    
    @classmethod
    def get_example_response(cls, business_type: str, intent: str) -> str:
        """Get example response for a business type and intent"""
        template = cls.get_template(business_type)
        examples = template.get("example_responses", {})
        return examples.get(intent, "")
