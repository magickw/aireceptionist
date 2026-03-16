"""Seed database with existing business templates from business_templates.py"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.models import BusinessTemplate, TemplateVersion, IntentClassification, BusinessTypeSuggestion

# Business template data extracted from business_templates.py
BUSINESS_TEMPLATES = {
    "restaurant": {
        "name": "Restaurant",
        "icon": "restaurant",
        "description": "Food service establishment with menu items and ordering",
        "autonomy_level": "HIGH",
        "risk_profile": {
            "high_risk_intents": ["refund_request", "food_allergy", "food_poisoning"],
            "auto_escalate_threshold": 0.7,
            "confidence_threshold": 0.5,
        },
        "common_intents": [
            "make_reservation", "order_food", "menu_inquiry", "dietary_options",
            "hours_inquiry", "location_inquiry", "takeout_order", "delivery_order",
            "special_request", "catering_inquiry", "reservation_inquiry"
        ],
        "fields": {
            "customer_name": {
                "required": False,
                "validation": "string",
                "prompt": "May I have your name for the order?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "delivery_method": {
                "required": False,
                "validation": "string",
                "prompt": "Would you like that for pickup or delivery?"
            },
            "address": {
                "required": False,
                "validation": "string",
                "prompt": "What's your delivery address?",
                "for_intents": ["delivery_order"]
            },
            "party_size": {
                "required": False,
                "validation": "string",
                "prompt": "How many people will be dining?",
                "for_intents": ["make_reservation"]
            },
            "reservation_time": {
                "required": True,
                "validation": "future_date",
                "prompt": "What time would you like to reserve?",
                "for_intents": ["make_reservation"]
            },
        },
        "booking_flow": {
            "type": "order",
            "steps": [
                {"field": "menu_item", "ask_if_missing": True},
                {"field": "quantity", "ask_if_missing": False, "default": 1},
                {"field": "delivery_method", "ask_if_missing": True},
                {"field": "customer_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
            ],
            "final_action": "PLACE_ORDER",
            "confirmation_message": "Your order has been placed. Total: ${total}. Ready for {delivery_method}.",
        },
        "system_prompt_addition": """
## Restaurant-Specific Guidelines:
- CRITICAL - PRICING: When customers ask about prices, provide EXACT price from Menu.
- When customer orders multiple items, ALWAYS calculate and provide the TOTAL price.
- After customer confirms items, THEN ask for name and phone
- Do NOT repeat information already provided
- Handle to-go orders and delivery inquiries
""",
        "example_responses": {
            "menu_inquiry": "We have {items} on our menu. Would you like to hear about any specific category?",
            "order_food": "Great choice! {item_name} is ${price}. Would you like anything else?",
            "make_reservation": "I can help with that. How many people and what time would you like to reserve?",
        }
    },
    "medical": {
        "name": "Medical Clinic",
        "icon": "local_hospital",
        "description": "Healthcare facility with appointment scheduling",
        "autonomy_level": "RESTRICTED",
        "risk_profile": {
            "high_risk_intents": ["medical_emergency", "severe_symptoms", "prescription_refill"],
            "auto_escalate_threshold": 0.3,
            "confidence_threshold": 0.85,
        },
        "common_intents": [
            "schedule_appointment", "inquire_services", "insurance_inquiry",
            "prescription_inquiry", "hours_inquiry", "location_inquiry",
            "doctor_availability", "new_patient_inquiry"
        ],
        "fields": {
            "patient_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have the patient's name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "reason_for_visit": {
                "required": True,
                "validation": "string",
                "prompt": "What is the reason for your visit?"
            },
            "appointment_time": {
                "required": True,
                "validation": "future_date",
                "prompt": "When would you like to schedule your appointment?"
            },
            "insurance_info": {
                "required": False,
                "validation": "string",
                "prompt": "Do you have insurance? If so, which provider?"
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "patient_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "reason_for_visit", "ask_if_missing": True},
                {"field": "appointment_time", "ask_if_missing": True},
                {"field": "insurance_info", "ask_if_missing": False},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your appointment is scheduled for {appointment_time} for {patient_name}. Please bring your insurance card.",
        },
        "system_prompt_addition": """
## Medical Clinic Guidelines:
- CRITICAL SAFETY: If customer mentions emergency, severe pain, bleeding, or heart symptoms, IMMEDIATELY escalate to human.
- Never provide medical advice or diagnosis.
- Always recommend consulting with a healthcare provider for medical questions.
- Prescription refills require doctor approval - do not promise.
- HIPAA compliance: Collect minimal necessary information.
""",
        "example_responses": {
            "schedule_appointment": "I can help schedule an appointment. What is the reason for your visit and when would you like to come in?",
            "inquire_services": "We offer general checkups, vaccinations, lab work, and specialist referrals. What type of service do you need?",
        }
    },
    "dental": {
        "name": "Dental Clinic",
        "icon": "cleaning_services",
        "description": "Dental care provider with appointment scheduling",
        "autonomy_level": "RESTRICTED",
        "risk_profile": {
            "high_risk_intents": ["dental_emergency", "severe_tooth_pain", "bleeding_gums"],
            "auto_escalate_threshold": 0.4,
            "confidence_threshold": 0.8,
        },
        "common_intents": [
            "schedule_appointment", "inquire_services", "insurance_inquiry",
            "teeth_cleaning", "checkup_inquiry", "hours_inquiry",
            "cosmetic_dentistry", "orthodontics_inquiry"
        ],
        "fields": {
            "patient_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have the patient's name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "service_type": {
                "required": True,
                "validation": "string",
                "prompt": "What type of dental service do you need? (cleaning, checkup, filling, etc.)"
            },
            "appointment_time": {
                "required": True,
                "validation": "future_date",
                "prompt": "When would you like to schedule your appointment?"
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "patient_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "service_type", "ask_if_missing": True},
                {"field": "appointment_time", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your dental appointment for {service_type} is scheduled for {appointment_time}. Please arrive 10 minutes early.",
        },
        "system_prompt_addition": """
## Dental Clinic Guidelines:
- CRITICAL SAFETY: Severe tooth pain, swelling, or bleeding should be escalated immediately.
- Never provide medical diagnosis or treatment advice.
- Emergency appointments may require same-day scheduling.
- Insurance verification may be required before appointment.
""",
        "example_responses": {
            "schedule_appointment": "I'd be happy to schedule your appointment. What type of dental service do you need?",
            "teeth_cleaning": "We offer professional teeth cleaning appointments. When would you like to come in?",
        }
    },
    "hotel": {
        "name": "Hotel",
        "icon": "hotel",
        "description": "Accommodation provider with room reservations",
        "autonomy_level": "MEDIUM",
        "risk_profile": {
            "high_risk_intents": ["billing_dispute", "safety_concern", "guest_complaint"],
            "auto_escalate_threshold": 0.6,
            "confidence_threshold": 0.6,
        },
        "common_intents": [
            "make_reservation", "check_availability", "room_inquiry",
            "amenities_inquiry", "cancellation_inquiry", "check_in_info",
            "pet_policy", "parking_inquiry"
        ],
        "fields": {
            "guest_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have the guest's name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "check_in_date": {
                "required": True,
                "validation": "future_date",
                "prompt": "What date would you like to check in?"
            },
            "check_out_date": {
                "required": True,
                "validation": "future_date",
                "prompt": "What date would you like to check out?"
            },
            "room_type": {
                "required": False,
                "validation": "string",
                "prompt": "What type of room would you prefer? (standard, deluxe, suite)"
            },
            "number_of_guests": {
                "required": False,
                "validation": "string",
                "prompt": "How many guests will be staying?"
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "check_in_date", "ask_if_missing": True},
                {"field": "check_out_date", "ask_if_missing": True},
                {"field": "room_type", "ask_if_missing": False},
                {"field": "number_of_guests", "ask_if_missing": False},
                {"field": "guest_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your reservation is confirmed for {check_in_date} to {check_out_date}. Check-in is at 3 PM.",
        },
        "system_prompt_addition": """
## Hotel Guidelines:
- Room availability must be checked before confirming reservations.
- Cancellation policies should be explained when booking.
- Special requests (early check-in, late check-out) may require approval.
- Pet policies vary by room type - verify availability.
""",
        "example_responses": {
            "make_reservation": "I can help with your reservation. What are your check-in and check-out dates?",
            "check_availability": "Let me check our availability. What dates are you looking at?",
        }
    },
    "law_firm": {
        "name": "Law Firm",
        "icon": "gavel",
        "description": "Legal services provider with consultation scheduling",
        "autonomy_level": "RESTRICTED",
        "risk_profile": {
            "high_risk_intents": ["legal_advice", "criminal_matter", "urgent_legal_issue"],
            "auto_escalate_threshold": 0.4,
            "confidence_threshold": 0.8,
        },
        "common_intents": [
            "schedule_consultation", "inquire_services", "fee_inquiry",
            "attorney_availability", "case_inquiry", "hours_inquiry"
        ],
        "fields": {
            "client_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "case_type": {
                "required": True,
                "validation": "string",
                "prompt": "What type of legal matter do you need assistance with?"
            },
            "consultation_time": {
                "required": True,
                "validation": "future_date",
                "prompt": "When would you like to schedule a consultation?"
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "client_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "case_type", "ask_if_missing": True},
                {"field": "consultation_time", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your legal consultation is scheduled for {consultation_time}. Please bring any relevant documents.",
        },
        "system_prompt_addition": """
## Law Firm Guidelines:
- CRITICAL CONFIDENTIALITY: Never discuss case details over phone without attorney-client relationship.
- Do not provide legal advice or opinions - only schedule consultations.
- Attorney confidentiality must be maintained.
- Urgent matters (court dates, arrests) require immediate escalation.
""",
        "example_responses": {
            "schedule_consultation": "I can schedule a consultation with an attorney. What type of legal matter do you need help with?",
            "inquire_services": "We offer consultations for family law, personal injury, criminal defense, and business law. What area do you need?",
        }
    },
    "salon": {
        "name": "Salon / Spa",
        "icon": "spa",
        "description": "Beauty and wellness services provider",
        "autonomy_level": "HIGH",
        "risk_profile": {
            "high_risk_intents": ["allergic_reaction", "service_complaint"],
            "auto_escalate_threshold": 0.7,
            "confidence_threshold": 0.5,
        },
        "common_intents": [
            "book_appointment", "service_inquiry", "stylist_availability",
            "pricing_inquiry", "hours_inquiry", "gift_card_inquiry"
        ],
        "fields": {
            "client_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "service_type": {
                "required": True,
                "validation": "string",
                "prompt": "What service would you like to book?"
            },
            "appointment_time": {
                "required": True,
                "validation": "future_date",
                "prompt": "When would you like to come in?"
            },
            "stylist_preference": {
                "required": False,
                "validation": "string",
                "prompt": "Do you have a stylist preference?"
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "service_type", "ask_if_missing": True},
                {"field": "appointment_time", "ask_if_missing": True},
                {"field": "stylist_preference", "ask_if_missing": False},
                {"field": "client_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your {service_type} appointment is scheduled for {appointment_time}. Please arrive 5 minutes early.",
        },
        "system_prompt_addition": """
## Salon/Spa Guidelines:
- Stylist availability must be checked before booking.
- Service duration varies - inform customer of time commitment.
- Allergic reactions to products - ask about sensitivities.
- Cancellation policy: 24-hour notice required.
""",
        "example_responses": {
            "book_appointment": "I'd love to help you book an appointment. What service are you interested in?",
            "service_inquiry": "We offer haircuts, coloring, manicures, pedicures, and facials. What sounds good to you?",
        }
    },
    "fitness": {
        "name": "Fitness Center",
        "icon": "fitness_center",
        "description": "Gym and fitness facility with membership and class booking",
        "autonomy_level": "HIGH",
        "risk_profile": {
            "high_risk_intents": ["injury_report", "equipment_issue"],
            "auto_escalate_threshold": 0.6,
            "confidence_threshold": 0.5,
        },
        "common_intents": [
            "membership_inquiry", "class_schedule", "book_class",
            "personal_training", "hours_inquiry", "amenities_inquiry"
        ],
        "fields": {
            "member_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "class_type": {
                "required": True,
                "validation": "string",
                "prompt": "Which class are you interested in?",
                "for_intents": ["book_class"]
            },
            "class_time": {
                "required": True,
                "validation": "future_date",
                "prompt": "When would you like to attend the class?",
                "for_intents": ["book_class"]
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "class_type", "ask_if_missing": True},
                {"field": "class_time", "ask_if_missing": True},
                {"field": "member_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your spot in {class_type} is reserved for {class_time}. Please arrive 5 minutes early.",
        },
        "system_prompt_addition": """
## Fitness Center Guidelines:
- Class size limits apply - check availability.
- New members may require orientation session.
- Personal training requires separate booking.
- Safety protocols for equipment use.
""",
        "example_responses": {
            "membership_inquiry": "We offer monthly, quarterly, and annual memberships. Would you like details on pricing?",
            "book_class": "I can book you into a class. Which class and when would you like to attend?",
        }
    },
    "real_estate": {
        "name": "Real Estate Agency",
        "icon": "home",
        "description": "Property sales and rental services",
        "autonomy_level": "MEDIUM",
        "risk_profile": {
            "high_risk_intents": ["legal_question", "contract_issue", "deposit_dispute"],
            "auto_escalate_threshold": 0.5,
            "confidence_threshold": 0.6,
        },
        "common_intents": [
            "property_inquiry", "schedule_viewing", "listing_inquiry",
            "rental_inquiry", "agent_availability", "mortgage_inquiry"
        ],
        "fields": {
            "client_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "property_interest": {
                "required": True,
                "validation": "string",
                "prompt": "What type of property are you looking for?"
            },
            "viewing_time": {
                "required": True,
                "validation": "future_date",
                "prompt": "When would you like to schedule a viewing?"
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "property_interest", "ask_if_missing": True},
                {"field": "viewing_time", "ask_if_missing": True},
                {"field": "client_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your property viewing is scheduled for {viewing_time}. An agent will contact you to confirm.",
        },
        "system_prompt_addition": """
## Real Estate Guidelines:
- Property availability must be verified before scheduling viewings.
- Pre-qualification may be required for showings.
- Do not provide legal advice on contracts or disclosures.
- Agent availability varies - confirm with agent before finalizing.
""",
        "example_responses": {
            "property_inquiry": "I can help you find properties. What type of property and what area are you interested in?",
            "schedule_viewing": "I'd be happy to schedule a viewing. Which property are you interested in and when works for you?",
        }
    },
    "hvac": {
        "name": "HVAC / Home Services",
        "icon": "handyman",
        "description": "Heating, ventilation, and air conditioning services",
        "autonomy_level": "MEDIUM",
        "risk_profile": {
            "high_risk_intents": ["gas_leak", "emergency_repair", "carbon_monoxide"],
            "auto_escalate_threshold": 0.4,
            "confidence_threshold": 0.6,
        },
        "common_intents": [
            "schedule_service", "repair_inquiry", "maintenance_inquiry",
            "installation_quote", "emergency_repair", "hours_inquiry"
        ],
        "fields": {
            "customer_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "service_type": {
                "required": True,
                "validation": "string",
                "prompt": "What type of service do you need? (repair, maintenance, installation)"
            },
            "address": {
                "required": True,
                "validation": "string",
                "prompt": "What is your service address?"
            },
            "appointment_time": {
                "required": True,
                "validation": "future_date",
                "prompt": "When would you like to schedule service?"
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "service_type", "ask_if_missing": True},
                {"field": "address", "ask_if_missing": True},
                {"field": "appointment_time", "ask_if_missing": True},
                {"field": "customer_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your {service_type} service is scheduled for {appointment_time}. A technician will arrive at {address}.",
        },
        "system_prompt_addition": """
## HVAC/Home Services Guidelines:
- CRITICAL SAFETY: Gas leak, carbon monoxide, or fire concerns require immediate human intervention.
- Emergency repairs may have priority scheduling.
- Service calls may require dispatch coordination.
- Provide safety instructions for emergencies.
""",
        "example_responses": {
            "schedule_service": "I can schedule service for you. What type of HVAC service do you need?",
            "emergency_repair": "For emergency repairs, I'll connect you with our dispatch team right away. What's the emergency?",
        }
    },
    "accounting": {
        "name": "Accounting / Tax Firm",
        "icon": "calculate",
        "description": "Financial and tax services provider",
        "autonomy_level": "RESTRICTED",
        "risk_profile": {
            "high_risk_intents": ["tax_advice", "irs_notice", "audit_inquiry"],
            "auto_escalate_threshold": 0.5,
            "confidence_threshold": 0.75,
        },
        "common_intents": [
            "schedule_consultation", "service_inquiry", "tax_filing_inquiry",
            "bookkeeping_inquiry", "payroll_inquiry", "hours_inquiry"
        ],
        "fields": {
            "client_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "service_type": {
                "required": True,
                "validation": "string",
                "prompt": "What type of accounting service do you need?"
            },
            "consultation_time": {
                "required": True,
                "validation": "future_date",
                "prompt": "When would you like to schedule a consultation?"
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "service_type", "ask_if_missing": True},
                {"field": "consultation_time", "ask_if_missing": True},
                {"field": "client_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your consultation for {service_type} is scheduled for {consultation_time}. Please bring relevant documents.",
        },
        "system_prompt_addition": """
## Accounting/Tax Firm Guidelines:
- Do not provide tax advice or financial recommendations without proper consultation.
- IRS notices and audits require immediate attorney/accountant escalation.
- Document requirements vary by service - inform client.
- Tax season may have limited availability.
""",
        "example_responses": {
            "schedule_consultation": "I can schedule a consultation with one of our accountants. What type of service do you need?",
            "service_inquiry": "We offer tax preparation, bookkeeping, payroll, and business consulting. What can I help you with?",
        }
    },
    "retail": {
        "name": "Retail Store",
        "icon": "shopping_cart",
        "description": "Retail business with product ordering",
        "autonomy_level": "HIGH",
        "risk_profile": {
            "high_risk_intents": ["refund_dispute", "fraud_report"],
            "auto_escalate_threshold": 0.6,
            "confidence_threshold": 0.5,
        },
        "common_intents": [
            "product_inquiry", "place_order", "availability_check",
            "hours_inquiry", "return_policy", "delivery_inquiry"
        ],
        "fields": {
            "customer_name": {
                "required": False,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "product": {
                "required": True,
                "validation": "string",
                "prompt": "Which product would you like to order?"
            },
            "quantity": {
                "required": False,
                "validation": "string",
                "prompt": "How many would you like?"
            },
            "delivery_method": {
                "required": False,
                "validation": "string",
                "prompt": "Would you like pickup or delivery?"
            },
        },
        "booking_flow": {
            "type": "order",
            "steps": [
                {"field": "product", "ask_if_missing": True},
                {"field": "quantity", "ask_if_missing": False},
                {"field": "delivery_method", "ask_if_missing": True},
                {"field": "customer_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
            ],
            "final_action": "PLACE_ORDER",
            "confirmation_message": "Your order for {product} (qty: {quantity}) has been placed. Total: ${total}.",
        },
        "system_prompt_addition": """
## Retail Store Guidelines:
- Product availability must be checked before confirming orders.
- Pricing should be exact - do not estimate.
- Return policy: 30 days with receipt for most items.
- Special orders may require deposit.
""",
        "example_responses": {
            "product_inquiry": "I can check on that for you. Which product are you looking for?",
            "place_order": "Great! {product} is ${price}. How many would you like?",
        }
    },
    "auto_repair": {
        "name": "Auto Repair Shop",
        "icon": "directions_car",
        "description": "Vehicle maintenance and repair services",
        "autonomy_level": "MEDIUM",
        "risk_profile": {
            "high_risk_intents": ["safety_recall", "brake_failure", "engine_failure"],
            "auto_escalate_threshold": 0.5,
            "confidence_threshold": 0.6,
        },
        "common_intents": [
            "schedule_service", "repair_inquiry", "maintenance_inquiry",
            "estimate_request", "hours_inquiry", "parts_inquiry"
        ],
        "fields": {
            "customer_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "vehicle_info": {
                "required": True,
                "validation": "string",
                "prompt": "What is your vehicle's make, model, and year?"
            },
            "service_type": {
                "required": True,
                "validation": "string",
                "prompt": "What type of service do you need?"
            },
            "appointment_time": {
                "required": True,
                "validation": "future_date",
                "prompt": "When would you like to bring your vehicle in?"
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "vehicle_info", "ask_if_missing": True},
                {"field": "service_type", "ask_if_missing": True},
                {"field": "appointment_time", "ask_if_missing": True},
                {"field": "customer_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your service appointment for {vehicle_info} is scheduled for {appointment_time}. Drop-off available at 7 AM.",
        },
        "system_prompt_addition": """
## Auto Repair Guidelines:
- Vehicle information is required for parts lookup.
- Safety concerns (brakes, steering, engine) require priority scheduling.
- Estimates are provided before work begins.
- Loaner vehicles may be available - inquire if needed.
""",
        "example_responses": {
            "schedule_service": "I can schedule service for you. What type of work does your vehicle need?",
            "repair_inquiry": "I'd be happy to help. What vehicle do you have and what seems to be the issue?",
        }
    },
    "education": {
        "name": "Education / Tutoring Center",
        "icon": "school",
        "description": "Educational services and tutoring",
        "autonomy_level": "HIGH",
        "risk_profile": {
            "high_risk_intents": ["safety_concern", "bullying_report"],
            "auto_escalate_threshold": 0.6,
            "confidence_threshold": 0.5,
        },
        "common_intents": [
            "enrollment_inquiry", "class_inquiry", "tutoring_request",
            "schedule_session", "hours_inquiry", "curriculum_inquiry"
        ],
        "fields": {
            "student_name": {
                "required": True,
                "validation": "string",
                "prompt": "What is the student's name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "subject": {
                "required": True,
                "validation": "string",
                "prompt": "What subject or grade level do you need help with?"
            },
            "session_time": {
                "required": True,
                "validation": "future_date",
                "prompt": "When would you like to schedule a session?"
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "student_name", "ask_if_missing": True},
                {"field": "subject", "ask_if_missing": True},
                {"field": "session_time", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your tutoring session for {subject} is scheduled for {session_time}. Please arrive 5 minutes early.",
        },
        "system_prompt_addition": """
## Education/Tutoring Guidelines:
- Age and grade level affect curriculum selection.
- Subject material may require tutor specialization.
- Session duration typically 60 minutes.
- Parent/guardian consent may be required for minors.
""",
        "example_responses": {
            "enrollment_inquiry": "I can help with enrollment. What grade level or subject area are you interested in?",
            "schedule_session": "I'd love to help with tutoring. What subject does the student need help with?",
        }
    },
    "pet_services": {
        "name": "Pet Services",
        "icon": "pets",
        "description": "Veterinary, grooming, and boarding services for pets",
        "autonomy_level": "HIGH",
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
            "pet_name": {
                "required": True,
                "validation": "string",
                "prompt": "What's your pet's name?"
            },
            "pet_type": {
                "required": True,
                "validation": "string",
                "prompt": "What kind of pet is it? (dog, cat, etc.)"
            },
            "service_type": {
                "required": True,
                "validation": "string",
                "prompt": "What service do you need?"
            },
            "appointment_time": {
                "required": True,
                "validation": "future_date",
                "prompt": "When would you like to schedule?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "pet_name", "ask_if_missing": True},
                {"field": "pet_type", "ask_if_missing": True},
                {"field": "service_type", "ask_if_missing": True},
                {"field": "appointment_time", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Confirmed! {pet_name} is scheduled for {service_type} on {appointment_time}.",
        },
        "system_prompt_addition": """
## Pet Services Guidelines:
- Collect pet name and type.
- For medical emergencies or aggressive behavior, escalate to human immediately.
- Mention current promotions if applicable.
""",
        "example_responses": {
            "book_grooming": "I'd be happy to book grooming for your pet. What's your pet's name and type?",
            "emergency_vet": "For medical emergencies, please bring your pet in immediately. I'll alert our veterinary team.",
        }
    },
    "banking": {
        "name": "Banking / Financial Institution",
        "icon": "account_balance",
        "description": "Banking services including accounts, loans, and financial products",
        "autonomy_level": "RESTRICTED",
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
            "customer_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "account_number": {
                "required": False,
                "validation": "account_number",
                "prompt": "What's your account number? (Last 4 digits for verification)",
                "for_intents": ["account_inquiry", "balance_inquiry", "transaction_inquiry"]
            },
            "service_type": {
                "required": True,
                "validation": "string",
                "prompt": "What banking service do you need?"
            },
            "preferred_date": {
                "required": False,
                "validation": "future_date",
                "prompt": "When would you like to visit the branch?",
                "for_intents": ["branch_appointment", "loan_application"]
            },
            "preferred_time": {
                "required": False,
                "validation": "string",
                "prompt": "What time works best?",
                "for_intents": ["branch_appointment", "loan_application"]
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "customer_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "service_type", "ask_if_missing": True},
                {"field": "account_number", "ask_if_missing": False},
                {"field": "preferred_date", "ask_if_missing": False},
                {"field": "preferred_time", "ask_if_missing": False},
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
    "insurance": {
        "name": "Insurance Agency",
        "icon": "security",
        "description": "Insurance services including claims, policies, and coverage",
        "autonomy_level": "RESTRICTED",
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
            "customer_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "policy_number": {
                "required": False,
                "validation": "policy_number",
                "prompt": "What's your policy number?"
            },
            "service_type": {
                "required": True,
                "validation": "string",
                "prompt": "What insurance service do you need?"
            },
            "claim_details": {
                "required": False,
                "validation": "string",
                "prompt": "Can you provide details about the incident?",
                "for_intents": ["file_claim"]
            },
            "preferred_date": {
                "required": False,
                "validation": "future_date",
                "prompt": "When would you like to meet with an agent?",
                "for_intents": ["agent_appointment"]
            },
            "preferred_time": {
                "required": False,
                "validation": "string",
                "prompt": "What time works best?",
                "for_intents": ["agent_appointment"]
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "customer_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "service_type", "ask_if_missing": True},
                {"field": "policy_number", "ask_if_missing": False},
                {"field": "claim_details", "ask_if_missing": False},
                {"field": "preferred_date", "ask_if_missing": False},
                {"field": "preferred_time", "ask_if_missing": False},
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
    "veterinary": {
        "name": "Veterinary Clinic",
        "icon": "local_veterinarian",
        "description": "Veterinary medical services for pets and animals",
        "autonomy_level": "RESTRICTED",
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
            "owner_name": {
                "required": True,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": True,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "pet_name": {
                "required": True,
                "validation": "string",
                "prompt": "What's your pet's name?"
            },
            "pet_type": {
                "required": True,
                "validation": "string",
                "prompt": "What type of pet is it? (dog, cat, etc.)"
            },
            "pet_breed": {
                "required": False,
                "validation": "string",
                "prompt": "What breed is your pet?"
            },
            "pet_age": {
                "required": False,
                "validation": "string",
                "prompt": "How old is your pet?"
            },
            "service_type": {
                "required": True,
                "validation": "string",
                "prompt": "What veterinary service do you need?"
            },
            "symptoms": {
                "required": False,
                "validation": "string",
                "prompt": "Can you describe your pet's symptoms?",
                "for_intents": ["symptoms_inquiry", "emergency_care"]
            },
            "preferred_date": {
                "required": True,
                "validation": "future_date",
                "prompt": "What date works for the appointment?"
            },
            "preferred_time": {
                "required": True,
                "validation": "string",
                "prompt": "What time works best?"
            },
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
                {"field": "symptoms", "ask_if_missing": False},
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
    "chiropractic": {
        "name": "Chiropractic Clinic",
        "icon": "accessibility_new",
        "description": "Healthcare facility specializing in musculoskeletal and nervous system health",
        "autonomy_level": "RESTRICTED",
        "risk_profile": {
            "high_risk_intents": ["severe_pain", "numbness_weakness", "loss_of_bladder_control", "trauma_injury", "cauda_equina_symptoms"],
            "auto_escalate_threshold": 0.3,
            "confidence_threshold": 0.85,
        },
        "common_intents": [
            "book_appointment", "back_pain", "neck_pain", "headache_relief",
            "sciatica_treatment", "joint_adjustment", "spinal_decompression",
            "sports_injury", "whiplash_treatment", "posture_correction",
            "wellness_adjustment", "first_visit_consultation", "insurance_inquiry"
        ],
        "fields": {
            "patient_name": {"required": True, "validation": "string", "prompt": "May I have your full name?"},
            "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
            "reason_for_visit": {"required": True, "validation": "string", "prompt": "What's the main reason for your visit today?"},
            "pain_level": {"required": False, "validation": "string", "prompt": "On a scale of 1-10, how would you rate your pain?"},
            "injury_onset": {"required": False, "validation": "string", "prompt": "When did this start? Was it sudden or gradual?"},
            "preferred_date": {"required": True, "validation": "future_date", "prompt": "What date works for your appointment?"},
            "preferred_time": {"required": True, "validation": "string", "prompt": "What time works best?"},
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "patient_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "reason_for_visit", "ask_if_missing": True},
                {"field": "pain_level", "ask_if_missing": False},
                {"field": "injury_onset", "ask_if_missing": False},
                {"field": "preferred_date", "ask_if_missing": True},
                {"field": "preferred_time", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your chiropractic appointment for {reason_for_visit} is confirmed for {preferred_date} at {preferred_time}. Please arrive 15 minutes early.",
        },
        "system_prompt_addition": """
## Chiropractic Clinic-Specific Guidelines:
- HIPAA compliance REQUIRED for all patient information.
- For severe symptoms (numbness, weakness, loss of bladder control) - ESCALATE IMMEDIATELY.
- **DO NOT provide medical diagnosis** - Only schedule appointments and explain chiropractic services.
- Explain what to expect: X-rays, examination, treatment plan development.
- Mention that first visits typically take 60-90 minutes.
- **DO NOT repeat questions** - Track collected information.
- Offer same-day appointments for acute pain when possible.
""",
        "example_responses": {
            "appointment": "I can schedule you with our chiropractor. What brings you in today?",
            "first_visit": "For your first visit, please arrive 15 minutes early. We'll do a comprehensive exam and discuss your treatment plan.",
            "emergency": "These symptoms require immediate medical attention. I'm connecting you with our doctor right away.",
        }
    },
    "physical_therapy": {
        "name": "Physical Therapy Clinic",
        "icon": "self_improvement",
        "description": "Rehabilitation facility for injury recovery and physical mobility",
        "autonomy_level": "RESTRICTED",
        "risk_profile": {
            "high_risk_intents": ["post_surgery_complications", "severe_pain", "fall_risk", "neurological_symptoms", "chest_pain"],
            "auto_escalate_threshold": 0.3,
            "confidence_threshold": 0.85,
        },
        "common_intents": [
            "book_evaluation", "post_surgery_rehab", "sports_injury", "back_pain",
            "neck_pain", "knee_pain", "shoulder_pain", "stroke_recovery",
            "balance_issues", "mobility_training", "manual_therapy",
            "therapeutic_exercise", "workers_compensation", "motor_vehicle_injury"
        ],
        "fields": {
            "patient_name": {"required": True, "validation": "string", "prompt": "May I have your full name?"},
            "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
            "condition_area": {"required": True, "validation": "string", "prompt": "What area needs treatment? (back, knee, shoulder, etc.)"},
            "referral_source": {"required": False, "validation": "string", "prompt": "Were you referred by a doctor?"},
            "preferred_date": {"required": True, "validation": "future_date", "prompt": "What date works for your evaluation?"},
            "preferred_time": {"required": True, "validation": "string", "prompt": "Morning, afternoon, or evening?"},
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "patient_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "condition_area", "ask_if_missing": True},
                {"field": "referral_source", "ask_if_missing": False},
                {"field": "preferred_date", "ask_if_missing": True},
                {"field": "preferred_time", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your physical therapy evaluation is scheduled for {preferred_date} at {preferred_time}. Please bring your referral.",
        },
        "system_prompt_addition": """
## Physical Therapy-Specific Guidelines:
- HIPAA compliance REQUIRED for all patient information.
- For post-surgery patients, confirm surgery date and restrictions.
- **DO NOT provide medical advice** - Only schedule evaluations and explain PT process.
- Mention that evaluations take 60 minutes.
- **DO NOT repeat questions** - Track collected information.
""",
        "example_responses": {
            "evaluation": "I'll schedule your initial evaluation. Our therapist will create a personalized treatment plan for you.",
            "post_surgery": "For post-surgery rehab, we'll coordinate with your surgeon's protocol. When was your surgery?",
        }
    },
    "optometry": {
        "name": "Optometry / Eye Care",
        "icon": "visibility",
        "description": "Comprehensive eye care facility with exams and optical shop",
        "autonomy_level": "RESTRICTED",
        "risk_profile": {
            "high_risk_intents": ["sudden_vision_loss", "eye_trauma", "chemical_exposure", "flashes_floaters_sudden", "eye_pain_severe"],
            "auto_escalate_threshold": 0.3,
            "confidence_threshold": 0.85,
        },
        "common_intents": [
            "comprehensive_eye_exam", "contact_lens_fitting", "glasses_exam",
            "dry_eye_treatment", "pink_eye", "glaucoma_screening",
            "cataract_consultation", "frame_selection", "emergency_eye_care"
        ],
        "fields": {
            "patient_name": {"required": True, "validation": "string", "prompt": "May I have your full name?"},
            "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
            "exam_type": {"required": True, "validation": "string", "prompt": "What type of exam do you need? (glasses, contacts, etc.)"},
            "vision_insurance": {"required": False, "validation": "string", "prompt": "Do you have vision insurance?"},
            "preferred_date": {"required": True, "validation": "future_date", "prompt": "What date works for your appointment?"},
            "preferred_time": {"required": True, "validation": "string", "prompt": "What time works best?"},
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "patient_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "exam_type", "ask_if_missing": True},
                {"field": "vision_insurance", "ask_if_missing": False},
                {"field": "preferred_date", "ask_if_missing": True},
                {"field": "preferred_time", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your {exam_type} is scheduled for {preferred_date} at {preferred_time}. Please bring your insurance card.",
        },
        "system_prompt_addition": """
## Optometry/Eye Care-Specific Guidelines:
- HIPAA compliance REQUIRED for all patient information.
- For sudden vision loss, trauma, or severe eye pain - ESCALATE IMMEDIATELY.
- Distinguish between medical eye exams and routine vision exams.
- **DO NOT provide medical diagnosis** - Only schedule and provide general info.
- **DO NOT repeat questions** - Track collected information.
""",
        "example_responses": {
            "comprehensive_exam": "I'll schedule your comprehensive eye exam. This includes checking your vision and eye health.",
            "emergency": "This sounds like an emergency. We have same-day slots available. Please come in immediately.",
        }
    },
    "urgent_care": {
        "name": "Urgent Care Center",
        "icon": "emergency",
        "description": "Immediate medical care for non-life-threatening conditions",
        "autonomy_level": "RESTRICTED",
        "risk_profile": {
            "high_risk_intents": ["chest_pain", "difficulty_breathing", "severe_bleeding", "stroke_symptoms", "unconscious", "seizure", "major_trauma", "suicidal_thoughts"],
            "auto_escalate_threshold": 0.2,
            "confidence_threshold": 0.9,
        },
        "common_intents": [
            "walk_in_visit", "minor_emergency", "fever_cold_flu", "sore_throat",
            "ear_infection", "UTI", "minor_cut_laceration", "sprain_strain",
            "vaccination_flu_shot", "drug_screening", "sports_physical"
        ],
        "fields": {
            "patient_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
            "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
            "symptoms": {"required": True, "validation": "string", "prompt": "What are your symptoms?"},
            "symptom_onset": {"required": False, "validation": "string", "prompt": "When did this start?"},
        },
        "booking_flow": {
            "type": "walk_in",
            "steps": [
                {"field": "patient_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "symptoms", "ask_if_missing": True},
                {"field": "symptom_onset", "ask_if_missing": False},
            ],
            "final_action": "PROVIDE_WAIT_TIME",
            "confirmation_message": "Thank you. Our current wait time is approximately {wait_time} minutes. No appointment needed.",
        },
        "system_prompt_addition": """
## Urgent Care-Specific Guidelines:
- HIPAA compliance REQUIRED for all patient information.
- CRITICAL TRIAGE: For chest pain, difficulty breathing, stroke symptoms (FAST) - ADVISE CALLING 911 IMMEDIATELY.
- **DO NOT provide medical diagnosis** - Only triage and provide wait times.
- Explain urgent care vs. ER: We handle non-life-threatening conditions.
- **DO NOT repeat questions** - Track collected information.
""",
        "example_responses": {
            "triage_safe": "Based on your symptoms, urgent care is appropriate. Current wait time is about 20 minutes.",
            "triage_emergency": "These symptoms could indicate a serious condition. Please call 911 immediately.",
        }
    },
    "car_dealership": {
        "name": "Car Dealership",
        "icon": "directions_car",
        "description": "Full-service automotive dealership for sales, service, and parts",
        "autonomy_level": "MEDIUM",
        "risk_profile": {
            "high_risk_intents": ["financing_inquiry", "trade_in_value", "price_negotiation", "test_drive_liability", "safety_recall"],
            "auto_escalate_threshold": 0.5,
            "confidence_threshold": 0.7,
        },
        "common_intents": [
            "schedule_test_drive", "service_appointment", "parts_inquiry",
            "inventory_check", "financing_options", "trade_in_inquiry",
            "sales_consultation", "hours_location", "lease_return",
            "recall_info", "roadside_assistance", "pricing_inquiry"
        ],
        "fields": {
            "customer_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
            "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
            "department": {"required": True, "validation": "string", "prompt": "Which department are you looking for? (Sales, Service, or Parts)"},
            "vehicle_interest": {"required": False, "validation": "string", "prompt": "Which vehicle model are you interested in?"},
            "preferred_date": {"required": True, "validation": "future_date", "prompt": "What date works best?"},
            "preferred_time": {"required": True, "validation": "string", "prompt": "What time would you prefer?"},
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "customer_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "department", "ask_if_missing": True},
                {"field": "preferred_date", "ask_if_missing": True},
                {"field": "preferred_time", "ask_if_missing": True},
            ],
            "final_action": "CREATE_APPOINTMENT",
            "confirmation_message": "Your {department} appointment is confirmed for {preferred_date} at {preferred_time}.",
        },
        "system_prompt_addition": """
## Car Dealership-Specific Guidelines:
- ROUTE BY DEPARTMENT: Sales, Service, or Parts.
- Sales: Schedule test drives and handle inventory inquiries. 
- Service: Schedule maintenance and handle recall inquiries.
- **DO NOT negotiate pricing** - Provide MSRP and offer a sales consultation for final pricing.
- For financing, explain basic options but escalate to Finance Manager.
""",
        "example_responses": {
            "test_drive": "I'd be happy to schedule a test drive. Which model are you interested in?",
            "service": "Our service department can help with that. When would you like to bring your vehicle in?",
        }
    },
    "grocery": {
        "name": "Grocery Store",
        "icon": "local_grocery_store",
        "description": "Supermarket with online ordering, delivery, and pickup services",
        "autonomy_level": "HIGH",
        "risk_profile": {
            "high_risk_intents": ["food_safety_complaint", "delivery_missing", "payment_error", "allergy_inquiry"],
            "auto_escalate_threshold": 0.6,
            "confidence_threshold": 0.5,
        },
        "common_intents": [
            "check_stock", "place_delivery_order", "curbside_pickup",
            "store_hours", "weekly_specials", "loyalty_points",
            "return_policy", "bakery_order", "deli_order"
        ],
        "fields": {
            "customer_name": {"required": True, "validation": "string", "prompt": "May I have your name for the order?"},
            "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
            "item_list": {"required": True, "validation": "string", "prompt": "What items would you like to order?"},
            "fulfillment_method": {"required": True, "validation": "string", "prompt": "Would you like delivery or curbside pickup?"},
        },
        "booking_flow": {
            "type": "order",
            "steps": [
                {"field": "customer_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "item_list", "ask_if_missing": True},
                {"field": "fulfillment_method", "ask_if_missing": True},
            ],
            "final_action": "PLACE_ORDER",
            "confirmation_message": "Your {fulfillment_method} order has been placed. We'll notify you when it's ready.",
        },
        "system_prompt_addition": """
## Grocery Store-Specific Guidelines:
- INVENTORY FOCUS: Help customers find if items are in stock.
- Handle delivery and curbside pickup requests.
- Mention weekly specials and loyalty program benefits.
- For food safety complaints, escalate to Store Manager immediately.
""",
        "example_responses": {
            "stock": "Let me check if we have that in stock for you...",
            "delivery": "I can help you place a delivery order. What do you need today?",
        }
    },
    "it_services": {
        "name": "IT Services",
        "icon": "computer",
        "description": "Technical support and managed IT services provider",
        "autonomy_level": "MEDIUM",
        "risk_profile": {
            "high_risk_intents": ["security_breach", "server_down", "data_loss", "urgent_fix", "password_reset_identity"],
            "auto_escalate_threshold": 0.4,
            "confidence_threshold": 0.75,
        },
        "common_intents": [
            "open_support_ticket", "check_ticket_status", "schedule_consultation",
            "hardware_repair", "software_install", "network_issue",
            "managed_services", "cybersecurity_audit", "emergency_support"
        ],
        "fields": {
            "customer_name": {"required": True, "validation": "string", "prompt": "May I have your name?"},
            "phone": {"required": True, "validation": "phone", "prompt": "What's the best number for a technician to call?"},
            "issue_description": {"required": True, "validation": "string", "prompt": "Can you briefly describe the issue?"},
            "urgency_level": {"required": True, "validation": "string", "prompt": "How urgent is this? (Low, Medium, High, Critical)"},
        },
        "booking_flow": {
            "type": "ticket",
            "steps": [
                {"field": "customer_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "issue_description", "ask_if_missing": True},
                {"field": "urgency_level", "ask_if_missing": True},
            ],
            "final_action": "OPEN_TICKET",
            "confirmation_message": "I've opened a support ticket. A technician will contact you based on your {urgency_level} urgency.",
        },
        "system_prompt_addition": """
## IT Services-Specific Guidelines:
- TRIAGE SPECIALIST: Determine urgency and type of issue.
- Critical issues (Server down, Security breach) MUST be escalated immediately.
- **DO NOT attempt technical fixes** - Your goal is to triage and route.
""",
        "example_responses": {
            "ticket": "I'll get a support ticket started for you. What's the problem?",
            "emergency": "Since your server is down, I'm escalating this to our emergency team right now.",
        }
    },
    "staffing_agency": {
        "name": "Staffing Agency",
        "icon": "groups",
        "description": "Recruitment and workforce solutions for employers and job seekers",
        "autonomy_level": "MEDIUM",
        "risk_profile": {
            "high_risk_intents": ["payroll_dispute", "harassment_report", "injury_on_job", "urgent_fulfillment"],
            "auto_escalate_threshold": 0.5,
            "confidence_threshold": 0.7,
        },
        "common_intents": [
            "job_search", "apply_for_job", "submit_timesheet",
            "hire_talent", "interview_scheduling", "payroll_inquiry",
            "onboarding_status", "temp_to_perm", "referral_program"
        ],
        "fields": {
            "full_name": {"required": True, "validation": "string", "prompt": "May I have your full name?"},
            "phone": {"required": True, "validation": "phone", "prompt": "What's the best number to reach you?"},
            "user_type": {"required": True, "validation": "string", "prompt": "Are you a job seeker or an employer looking to hire?"},
            "industry_focus": {"required": True, "validation": "string", "prompt": "Which industry are you focused on?"},
        },
        "booking_flow": {
            "type": "application",
            "steps": [
                {"field": "full_name", "ask_if_missing": True},
                {"field": "phone", "ask_if_missing": True},
                {"field": "user_type", "ask_if_missing": True},
                {"field": "industry_focus", "ask_if_missing": True},
            ],
            "final_action": "CREATE_LEAD",
            "confirmation_message": "Thank you! A recruiter specializing in {industry_focus} will contact you shortly.",
        },
        "system_prompt_addition": """
## Staffing Agency-Specific Guidelines:
- TWO-SIDED MARKET: Identify if caller is a Candidate (Job Seeker) or a Client (Employer).
- For payroll disputes or workplace injuries, escalate immediately.
- **DO NOT guarantee placement** - Explain recruiters will review applications.
""",
        "example_responses": {
            "candidate": "We have several openings in {industry_focus}. What kind of role are you looking for?",
            "employer": "I can help you find talent for your team. What industry are you hiring for?",
        }
    },
    "general": {
        "name": "General Business",
        "icon": "business",
        "description": "Default template for general business inquiries",
        "autonomy_level": "MEDIUM",
        "risk_profile": {
            "high_risk_intents": ["legal_question", "safety_concern"],
            "auto_escalate_threshold": 0.5,
            "confidence_threshold": 0.6,
        },
        "common_intents": [
            "hours_inquiry", "location_inquiry", "service_inquiry",
            "contact_info", "appointment_inquiry", "general_question"
        ],
        "fields": {
            "customer_name": {
                "required": False,
                "validation": "string",
                "prompt": "May I have your name?"
            },
            "phone": {
                "required": False,
                "validation": "phone",
                "prompt": "What's the best number to reach you?"
            },
            "inquiry_details": {
                "required": True,
                "validation": "string",
                "prompt": "How can I help you today?"
            },
        },
        "booking_flow": {
            "type": "appointment",
            "steps": [
                {"field": "inquiry_details", "ask_if_missing": True},
                {"field": "customer_name", "ask_if_missing": False},
                {"field": "phone", "ask_if_missing": False},
            ],
            "final_action": "PROVIDE_INFO",
            "confirmation_message": "Thank you for your inquiry. Someone will follow up with you shortly.",
        },
        "system_prompt_addition": """
## General Business Guidelines:
- Provide helpful information about hours, location, and services.
- Take detailed messages for callbacks.
- Escalate complex inquiries to human staff.
- Maintain professional and courteous tone.
""",
        "example_responses": {
            "hours_inquiry": "Our hours are Monday through Friday, 9 AM to 5 PM. We're closed on weekends.",
            "service_inquiry": "We offer a variety of services. What specifically are you looking for?",
        }
    },
}

# Business type suggestion keywords/phrases
BUSINESS_TYPE_SUGGESTIONS = {
    "restaurant": {
        "keywords": ["menu", "food", "dining", "eat", "restaurant", "cafe", "bistro", "grill", "kitchen", "chef", "cuisine", "takeout", "delivery", "dishes", "meal", "lunch", "dinner", "breakfast", "brunch", "appetizer", "entree", "dessert", "drink", "beverage"],
        "phrases": ["serving food", "food service", "dining establishment", "restaurant business", "cafe", "eatery", "food preparation", "kitchen", "chef", "catering", "takeout", "delivery service", "dishes", "menu items", "meals", "lunch", "dinner", "breakfast", "brunch"],
    },
    "medical": {
        "keywords": ["clinic", "medical", "health", "doctor", "physician", "healthcare", "hospital", "medical center", "health clinic", "healthcare provider", "medicine", "treatment", "diagnosis", "patient", "prescription", "pharmacy", "lab", "xray", "imaging", "surgery", "urgent care", "primary care", "specialist"],
        "phrases": ["medical clinic", "healthcare center", "doctor's office", "medical practice", "healthcare provider", "medical services", "patient care", "medical treatment", "health services", "physician practice", "urgent care", "primary care", "medical center"],
    },
    "dental": {
        "keywords": ["dental", "dentist", "teeth", "tooth", "oral", "hygiene", "cleaning", "filling", "crown", "bridge", "implant", "orthodontics", "braces", "root canal", "gum", "dental care", "dental clinic", "dental practice", "cosmetic dentistry"],
        "phrases": ["dental clinic", "dentist office", "dental practice", "dental care", "dental services", "teeth cleaning", "dental hygiene", "oral health", "dental treatment", "cosmetic dentistry", "orthodontics", "dental implants"],
    },
    "hotel": {
        "keywords": ["hotel", "motel", "inn", "lodge", "resort", "accommodation", "lodging", "guest", "room", "suite", "booking", "reservation", "check-in", "check-out", "amenities", "hospitality", "overnight", "stay", "vacation", "travel", "tourist"],
        "phrases": ["hotel accommodation", "lodging services", "guest rooms", "hotel booking", "hotel reservation", "hospitality services", "overnight stay", "vacation accommodation", "travel lodging", "hotel amenities", "guest services"],
    },
    "law_firm": {
        "keywords": ["law", "legal", "attorney", "lawyer", "law firm", "legal services", "legal advice", "counsel", "litigation", "contract", "legal representation", "legal practice", "advocate", "barrister", "solicitor", "jurisdiction", "court", "lawsuit", "legal counsel"],
        "phrases": ["law firm", "legal practice", "legal services", "attorney services", "legal representation", "legal counsel", "law office", "legal advice", "litigation services", "contract law", "legal advocacy", "court representation"],
    },
    "salon": {
        "keywords": ["salon", "spa", "beauty", "hair", "hairstyle", "haircut", "coloring", "stylist", "manicure", "pedicure", "facial", "massage", "wellness", "beauty salon", "hair salon", "day spa", "nail salon", "cosmetology", "skincare", "relaxation"],
        "phrases": ["beauty salon", "hair salon", "day spa", "nail salon", "beauty services", "hair styling", "haircut", "hair coloring", "manicure", "pedicure", "facial treatment", "massage therapy", "wellness center", "skincare", "cosmetology"],
    },
    "fitness": {
        "keywords": ["fitness", "gym", "workout", "exercise", "health club", "personal training", "trainer", "cardio", "strength", "yoga", "pilates", "fitness center", "health and wellness", "exercise classes", "gym membership", "fitness training", "weight loss", "muscle", "athletic"],
        "phrases": ["fitness center", "gym membership", "health club", "personal training", "exercise classes", "workout facility", "fitness training", "gym services", "health and wellness", "cardio training", "strength training", "yoga classes", "pilates classes"],
    },
    "real_estate": {
        "keywords": ["real estate", "property", "home", "house", "apartment", "condo", "rental", "rent", "lease", "buy", "sell", "listing", "agent", "broker", "realtor", "housing", "residential", "commercial", "mortgage", "property management", "viewing"],
        "phrases": ["real estate agency", "property sales", "rental properties", "home buying", "home selling", "real estate agent", "property listing", "real estate services", "residential property", "commercial property", "property management", "mortgage services", "home viewing"],
    },
    "hvac": {
        "keywords": ["hvac", "heating", "cooling", "air conditioning", "ventilation", "furnace", "ac", "air conditioner", "heat pump", "thermostat", "ductwork", "repair", "maintenance", "installation", "home services", "climate control", "temperature control", "mechanical", "plumbing"],
        "phrases": ["hvac services", "heating and cooling", "air conditioning repair", "furnace repair", "ac installation", "hvac maintenance", "home comfort services", "climate control", "temperature control", "mechanical services", "home repair", "heating system", "cooling system"],
    },
    "accounting": {
        "keywords": ["accounting", "accountant", "tax", "taxation", "tax preparation", "bookkeeping", "payroll", "financial", "finance", "audit", "cpa", "certified public accountant", "tax filing", "tax return", "financial services", "accounting services", "financial reporting", "tax advisor", "business accounting"],
        "phrases": ["accounting firm", "tax preparation", "bookkeeping services", "payroll services", "financial services", "tax filing", "tax return", "cpa services", "accounting services", "financial consulting", "tax advisor", "business accounting", "financial reporting"],
    },
    "retail": {
        "keywords": ["retail", "store", "shop", "shopping", "product", "merchandise", "inventory", "sales", "customer", "retailer", "retail store", "online store", "e-commerce", "point of sale", "cashier", "checkout", "return", "refund", "exchange", "discount", "promotion"],
        "phrases": ["retail store", "shopping center", "retail business", "product sales", "merchandise", "retail services", "customer service", "retail operations", "store management", "inventory management", "point of sale", "customer returns", "retail promotions"],
    },
    "auto_repair": {
        "keywords": ["auto", "automotive", "car", "vehicle", "repair", "maintenance", "mechanic", "service", "garage", "shop", "automotive repair", "car repair", "vehicle service", "oil change", "brake", "engine", "transmission", "tire", "alignment", "inspection", "diagnostics"],
        "phrases": ["auto repair shop", "automotive services", "car repair", "vehicle maintenance", "mechanic shop", "auto service", "garage services", "automotive repair", "vehicle repair", "car maintenance", "oil change", "brake service", "engine repair", "tire service", "auto diagnostics"],
    },
    "education": {
        "keywords": ["education", "school", "tutoring", "teaching", "learning", "academic", "student", "teacher", "instructor", "curriculum", "course", "class", "lesson", "training", "educational", "study", "learn", "knowledge", "skills", "tutor", "education center", "learning center"],
        "phrases": ["education center", "tutoring services", "learning center", "academic services", "educational programs", "teaching", "student support", "curriculum development", "course instruction", "skills training", "educational consulting", "tutor", "study help"],
    },
    "pet_services": {
        "keywords": ["pet", "dog", "cat", "animal", "veterinary", "vet", "grooming", "boarding", "kennel", "walking", "training", "puppy", "kitten", "pets", "pet care", "animal hospital"],
        "phrases": ["pet services", "veterinary clinic", "dog grooming", "cat boarding", "pet training", "pet walking", "animal care", "vet office", "kennel services", "pet grooming"],
    },
    "banking": {
        "keywords": ["bank", "banking", "financial", "credit union", "savings", "checking", "loan", "mortgage", "investment", "atm", "debit", "credit card", "wire transfer", "account", "deposit", "withdrawal", "branch", "teller", "finance"],
        "phrases": ["banking services", "financial institution", "credit union", "savings account", "checking account", "bank loan", "mortgage loan", "investment services", "atm services", "bank branch", "financial services"],
    },
    "insurance": {
        "keywords": ["insurance", "coverage", "policy", "premium", "claim", "deductible", "underwriting", "risk", "liability", "auto insurance", "home insurance", "life insurance", "health insurance", "insurance agency", "insurance broker", "insurance agent"],
        "phrases": ["insurance services", "insurance policy", "insurance coverage", "insurance claim", "insurance premium", "insurance agency", "insurance broker", "file a claim", "insurance quote", "deductible", "liability coverage"],
    },
    "veterinary": {
        "keywords": ["veterinary", "veterinarian", "vet", "animal hospital", "vet clinic", "animal doctor", "pet health", "animal healthcare", "vet practice", "veterinary medicine", "vet services", "pet clinic", "animal clinic"],
        "phrases": ["veterinary clinic", "veterinary hospital", "veterinary services", "animal hospital", "veterinary practice", "vet clinic", "pet health", "animal healthcare", "veterinary care"],
    },
    "chiropractic": {
        "keywords": ["chiropractic", "chiropractor", "back pain", "neck pain", "adjustment", "spinal", "alignment", "posture", "wellness", "sciatica", "headache", "whiplash", "joint pain", "subluxation"],
        "phrases": ["chiropractic clinic", "spinal adjustment", "back pain relief", "chiropractor office", "wellness adjustment", "chiropractic care", "neck pain treatment", "posture correction"],
    },
    "physical_therapy": {
        "keywords": ["physical therapy", "pt", "physiotherapy", "rehabilitation", "rehab", "injury", "mobility", "exercise", "strength", "balance", "stroke recovery", "post-surgery", "sports medicine", "manual therapy"],
        "phrases": ["physical therapy clinic", "rehabilitation center", "pt evaluation", "post-surgery rehab", "mobility training", "physical therapy services", "sports injury rehab", "physiotherapy office"],
    },
    "optometry": {
        "keywords": ["optometry", "optometrist", "eye", "vision", "glasses", "contacts", "contact lens", "exam", "ophthalmology", "lasik", "cataract", "glaucoma", "dry eye", "eye doctor"],
        "phrases": ["optometry clinic", "eye exam", "vision care", "contact lens fitting", "optometrist office", "eye care center", "glasses exam", "ophthalmic services"],
    },
    "urgent_care": {
        "keywords": ["urgent care", "walk-in", "minor emergency", "fever", "flu", "sore throat", "infection", "injury", "medical", "clinic", "treatment", "emergency", "sick", "doctor"],
        "phrases": ["urgent care center", "walk-in clinic", "medical treatment", "minor emergency care", "urgent medical care", "acute care", "immediate care", "healthcare clinic"],
    },
    "car_dealership": {
        "keywords": ["car dealership", "auto sales", "car dealer", "vehicle sales", "test drive", "buy a car", "used cars", "new cars", "car service", "auto repair", "dealership parts"],
        "phrases": ["car dealership", "auto dealer", "sales department", "service department", "parts department", "schedule test drive", "vehicle inventory", "car financing"],
    },
    "grocery": {
        "keywords": ["grocery", "supermarket", "food store", "grocery delivery", "curbside pickup", "check stock", "weekly specials", "grocery items", "shopping list", "bakery", "deli"],
        "phrases": ["grocery store", "supermarket", "grocery delivery", "curbside pickup", "food shopping", "check availability", "weekly ad", "bakery order", "deli counter"],
    },
    "it_services": {
        "keywords": ["it services", "tech support", "computer repair", "network issues", "managed it", "cybersecurity", "software install", "support ticket", "help desk", "it consulting"],
        "phrases": ["it services", "technical support", "managed it services", "tech support help desk", "open support ticket", "it consulting", "cybersecurity services"],
    },
    "staffing_agency": {
        "keywords": ["staffing agency", "recruitment", "headhunter", "temp agency", "hiring", "job search", "apply for job", "employment agency", "talent acquisition", "timesheet"],
        "phrases": ["staffing agency", "recruitment firm", "employment agency", "hire talent", "job application", "staffing solutions", "recruiting services"],
    },
}


def seed_templates(db: Session):
    """Seed business templates into database"""
    for template_key, template_data in BUSINESS_TEMPLATES.items():
        existing = db.query(BusinessTemplate).filter(
            BusinessTemplate.template_key == template_key
        ).first()
        
        if existing:
            print(f"Template '{template_key}' already exists, skipping...")
            continue
        
        template = BusinessTemplate(
            template_key=template_key,
            name=template_data["name"],
            icon=template_data["icon"],
            description=template_data["description"],
            autonomy_level=template_data["autonomy_level"],
            high_risk_intents=template_data["risk_profile"]["high_risk_intents"],
            auto_escalate_threshold=template_data["risk_profile"]["auto_escalate_threshold"],
            confidence_threshold=template_data["risk_profile"]["confidence_threshold"],
            common_intents=template_data["common_intents"],
            fields=template_data["fields"],
            booking_flow=template_data["booking_flow"],
            system_prompt_addition=template_data["system_prompt_addition"],
            example_responses=template_data["example_responses"],
            is_active=True,
            is_default=(template_key == "general"),
            version=1,
        )
        
        db.add(template)
        print(f"Added template: {template_key}")
    
    db.commit()
    print(f"\nSeeded {len(BUSINESS_TEMPLATES)} business templates")


def seed_suggestions(db: Session):
    """Seed business type suggestions into database"""
    for business_type, suggestion_data in BUSINESS_TYPE_SUGGESTIONS.items():
        existing = db.query(BusinessTypeSuggestion).filter(
            BusinessTypeSuggestion.business_type == business_type
        ).first()
        
        if existing:
            print(f"Suggestion for '{business_type}' already exists, skipping...")
            continue
        
        suggestion = BusinessTypeSuggestion(
            business_type=business_type,
            keywords=suggestion_data["keywords"],
            phrases=suggestion_data["phrases"],
            confidence_weight=1.0,
            is_active=True,
        )
        
        db.add(suggestion)
        print(f"Added suggestion: {business_type}")
    
    db.commit()
    print(f"\nSeeded {len(BUSINESS_TYPE_SUGGESTIONS)} business type suggestions")


def main():
    db = SessionLocal()
    try:
        print("Seeding business templates...")
        seed_templates(db)
        
        print("\nSeeding business type suggestions...")
        seed_suggestions(db)
        
        print("\n✅ Database seeding completed successfully!")
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()