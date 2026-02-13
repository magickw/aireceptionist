-- Mock Data for Nova Autonomous Business Agent Demo
-- This script populates the database with realistic demo data

-- Clear existing data (truncate in correct order due to foreign keys)
TRUNCATE TABLE conversation_messages CASCADE;
TRUNCATE TABLE call_sessions CASCADE;
TRUNCATE TABLE appointments CASCADE;
TRUNCATE TABLE ai_training_scenarios CASCADE;
TRUNCATE TABLE integrations CASCADE;
TRUNCATE TABLE businesses CASCADE;
TRUNCATE TABLE users CASCADE;

-- Insert Demo User (Business Owner)
INSERT INTO users (name, email, password, role, status, phone, created_at, updated_at) VALUES
('Dr. Sarah Johnson', 'sarah.johnson@smilecare.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4V5yQWZ5qZ1.9Z2e', 'business_owner', 'active', '+1 (555) 100-2000', NOW() - INTERVAL '6 months', NOW());

-- Insert Demo Business
INSERT INTO businesses (user_id, name, type, phone, address, description, website, status, operating_hours, created_at, updated_at) VALUES
(1, 'Smile Care Dental', 'dental', '+1 (555) 100-2000', '123 Dental Plaza, San Francisco, CA 94102', 
'Premium dental care with modern technology and compassionate care. Specializing in cosmetic dentistry, preventative care, and emergency services.',
'https://smilecaredental.com', 'active',
'{"0": {"open": 9, "close": 17, "closed": true}, "1": {"open": 9, "close": 18, "closed": false}, "2": {"open": 9, "close": 18, "closed": false}, "3": {"open": 9, "close": 18, "closed": false}, "4": {"open": 9, "close": 18, "closed": false}, "5": {"open": 9, "close": 15, "closed": false}, "6": {"open": 10, "close": 16, "closed": false}}',
NOW() - INTERVAL '6 months', NOW());

-- Insert AI Training Scenarios
INSERT INTO ai_training_scenarios (business_id, title, description, category, user_input, expected_response, is_active, success_rate, last_tested, created_at, updated_at) VALUES
(1, 'Dental Cleaning Booking', 'Customer wants to book a routine dental cleaning', 'Booking', 
'Hi, I''d like to schedule a dental cleaning for next week.',
'Perfect! I can help you schedule a dental cleaning. Do you have a preference for morning or afternoon appointments next week? We have availability Monday through Friday.',
true, 95.5, NOW() - INTERVAL '1 day', NOW() - INTERVAL '2 months', NOW()),

(1, 'Emergency Appointment', 'Customer has a dental emergency', 'Support',
'I have a severe toothache and need to see someone immediately.',
'I understand this is urgent. Let me check for the earliest available appointment today. Based on our schedule, Dr. Johnson has an opening at 2:30 PM. Would that work for you?',
true, 92.0, NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 months', NOW()),

(1, 'Service Inquiry', 'Customer asks about available services', 'Information',
'What dental services do you offer?',
'At Smile Care Dental, we offer comprehensive dental services including preventative care, cleanings, fillings, crowns, bridges, teeth whitening, Invisalign, emergency dental care, and cosmetic procedures. Is there a specific service you''re interested in?',
true, 98.0, NOW() - INTERVAL '1 week', NOW() - INTERVAL '2 months', NOW()),

(1, 'Pricing Inquiry', 'Customer asks about service pricing', 'Information',
'How much does a teeth whitening procedure cost?',
'Our teeth whitening treatment starts at $299 for the initial procedure. This includes a consultation, professional whitening session, and take-home maintenance kit. We also offer package discounts for multiple treatments.',
true, 94.0, NOW() - INTERVAL '5 days', NOW() - INTERVAL '2 months', NOW()),

(1, 'Reschedule Request', 'Customer wants to reschedule existing appointment', 'Booking',
'I need to reschedule my appointment from Friday to Monday.',
'I can help you reschedule that appointment. Let me check available slots for Monday. We have openings at 10:00 AM and 2:00 PM. Which time would work better for you?',
true, 91.5, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 months', NOW()),

(1, 'Insurance Inquiry', 'Customer asks about insurance acceptance', 'Information',
'Do you accept Delta Dental insurance?',
'Yes, we accept most major dental insurance plans including Delta Dental, Aetna, Cigna, MetLife, and United Healthcare. We can verify your coverage and handle claims directly with your insurance provider.',
true, 96.5, NOW() - INTERVAL '1 week', NOW() - INTERVAL '2 months', NOW());

-- Insert Demo Call Sessions with realistic data
INSERT INTO call_sessions (id, business_id, customer_phone, status, started_at, ended_at, duration_seconds, ai_confidence, summary, created_at) VALUES
('call_001', 1, '+1 (555) 234-5678', 'completed', NOW() - INTERVAL '3 hours', NOW() - INTERVAL '3 hours' + INTERVAL '127 seconds', 127, 0.94, 
'Customer Sarah Miller called to book a dental cleaning. Nova 2 Lite identified the intent, extracted service and date preferences, and successfully scheduled appointment. Customer expressed satisfaction with the quick booking process.',
NOW() - INTERVAL '3 hours'),

('call_002', 1, '+1 (555) 345-6789', 'completed', NOW() - INTERVAL '6 hours', NOW() - INTERVAL '6 hours' + INTERVAL '89 seconds', 89, 0.97,
'Customer John Davis had a question about teeth whitening pricing. Nova provided detailed pricing information and package options. Customer decided to book a consultation.',
NOW() - INTERVAL '6 hours'),

('call_003', 1, '+1 (555) 456-7890', 'completed', NOW() - INTERVAL '12 hours', NOW() - INTERVAL '12 hours' + INTERVAL '156 seconds', 156, 0.92,
'Customer Emily Chen needed to reschedule her appointment. Nova successfully found alternative slots and confirmed the new time. Customer was happy with the flexible rescheduling.',
NOW() - INTERVAL '12 hours'),

('call_004', 1, '+1 (555) 567-8901', 'completed', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' + INTERVAL '98 seconds', 98, 0.96,
'Customer Michael Brown inquired about insurance coverage. Nova provided comprehensive information about accepted plans and offered to verify coverage.',
NOW() - INTERVAL '1 day'),

('call_005', 1, '+1 (555) 678-9012', 'completed', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' + INTERVAL '210 seconds', 210, 0.88,
'Customer Jessica Wilson had a dental emergency. Nova prioritized the call, identified urgency, and scheduled same-day appointment. Customer expressed relief at quick response.',
NOW() - INTERVAL '1 day'),

('call_006', 1, '+1 (555) 789-0123', 'completed', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' + INTERVAL '115 seconds', 115, 0.95,
'Customer David Lee wanted to know about available services. Nova provided comprehensive service overview. Customer asked for pricing details on cosmetic procedures.',
NOW() - INTERVAL '2 days'),

('call_007', 1, '+1 (555) 890-1234', 'completed', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' + INTERVAL '78 seconds', 78, 0.93,
'Customer Amanda Garcia called to confirm her upcoming appointment. Nova verified the appointment details and provided pre-appointment instructions.',
NOW() - INTERVAL '2 days'),

('call_008', 1, '+1 (555) 901-2345', 'completed', NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days' + INTERVAL '145 seconds', 145, 0.91,
'Customer Robert Martinez had a complaint about wait time on previous visit. Nova acknowledged the concern, apologized, and offered priority scheduling for next appointment.',
NOW() - INTERVAL '3 days'),

('call_009', 1, '+1 (555) 012-3456', 'completed', NOW() - INTERVAL '4 days', NOW() - INTERVAL '4 days' + INTERVAL '92 seconds', 92, 0.96,
'Customer Lisa Anderson called to book Invisalign consultation. Nova identified the specific service requirement and scheduled consultation with orthodontist.',
NOW() - INTERVAL '4 days'),

('call_010', 1, '+1 (555) 123-4567', 'completed', NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days' + INTERVAL '168 seconds', 168, 0.89,
'Customer Christopher Taylor wanted to reschedule due to work conflict. Nova found alternative time slots and confirmed new appointment without issues.',
NOW() - INTERVAL '5 days');

-- Insert Conversation Messages for realistic transcripts
INSERT INTO conversation_messages (call_session_id, sender, content, message_type, confidence, intent, entities, timestamp) VALUES
-- Call 001: Booking
('call_001', 'customer', 'Hi, I''d like to book a dental cleaning for next week.', 'text', 0.94, 'appointment_booking', '{"service": "dental cleaning", "timeframe": "next week"}', NOW() - INTERVAL '3 hours'),
('call_001', 'ai', 'Perfect! I can help you schedule a dental cleaning. Do you have a preference for morning or afternoon appointments next week? We have availability Monday through Friday.', 'text', 0.96, 'information_gathering', NULL, NOW() - INTERVAL '3 hours' + INTERVAL '1 second'),
('call_001', 'customer', 'Afternoon would be better. How about Tuesday at 3 PM?', 'text', 0.95, 'appointment_booking', '{"date": "Tuesday", "time": "3 PM"}', NOW() - INTERVAL '3 hours' + INTERVAL '2 seconds'),
('call_001', 'ai', 'Great! Tuesday at 3 PM is available. I''ve booked you for a dental cleaning with Dr. Johnson. You''ll receive a confirmation shortly with pre-appointment instructions. Is there anything else I can help you with?', 'text', 0.98, 'confirmation', '{"date": "Tuesday", "time": "3 PM", "doctor": "Dr. Johnson"}', NOW() - INTERVAL '3 hours' + INTERVAL '3 seconds'),

-- Call 002: Pricing Inquiry
('call_002', 'customer', 'Hello, I''m interested in teeth whitening. How much does it cost?', 'text', 0.92, 'pricing_inquiry', '{"service": "teeth whitening"}', NOW() - INTERVAL '6 hours'),
('call_002', 'ai', 'Welcome to Smile Care Dental! Our teeth whitening treatment starts at $299 for the initial procedure. This includes a consultation, professional whitening session, and take-home maintenance kit. We also offer package discounts for multiple treatments.', 'text', 0.97, 'information_providing', '{"price": "$299", "includes": ["consultation", "whitening session", "maintenance kit"]}', NOW() - INTERVAL '6 hours' + INTERVAL '1 second'),
('call_002', 'customer', 'That sounds good. Do you offer any discounts?', 'text', 0.94, 'pricing_inquiry', NULL, NOW() - INTERVAL '6 hours' + INTERVAL '2 seconds'),
('call_002', 'ai', 'Yes! We offer 15% off when you book two or more treatments together. Additionally, new patients receive a $50 discount on their first whitening session. Would you like to schedule a consultation to see if teeth whitening is right for you?', 'text', 0.96, 'offer_promotion', '{"discount": "15%", "new_patient_discount": "$50"}', NOW() - INTERVAL '6 hours' + INTERVAL '3 seconds'),

-- Call 005: Emergency
('call_005', 'customer', 'Help! I have a terrible toothache and need to see someone right away!', 'text', 0.98, 'emergency', '{"urgency": "high", "complaint": "toothache"}', NOW() - INTERVAL '1 day'),
('call_005', 'ai', 'I understand this is urgent and I''m here to help. Based on our schedule, Dr. Johnson has an opening today at 3:45 PM. This is an emergency slot reserved for urgent cases. Should I book this appointment for you?', 'text', 0.95, 'emergency_handling', '{"date": "today", "time": "3:45 PM", "doctor": "Dr. Johnson"}', NOW() - INTERVAL '1 day' + INTERVAL '1 second'),
('call_005', 'customer', 'Yes, please book it. I''ll be there.', 'text', 0.96, 'confirmation', NULL, NOW() - INTERVAL '1 day' + INTERVAL '2 seconds'),
('call_005', 'ai', 'Perfect! I''ve booked your emergency appointment for today at 3:45 PM. When you arrive, please mention it''s an emergency so we can prioritize you. Is there anything specific about the pain I should note for Dr. Johnson?', 'text', 0.94, 'follow_up', NULL, NOW() - INTERVAL '1 day' + INTERVAL '3 seconds'),
('call_005', 'customer', 'It''s my lower left molar and it''s been throbbing for two days.', 'text', 0.92, 'symptom_reporting', '{"location": "lower left molar", "duration": "2 days"}', NOW() - INTERVAL '1 day' + INTERVAL '4 seconds'),
('call_005', 'ai', 'Thank you for that information. I''ve noted it for Dr. Johnson. She''ll be able to assess and provide immediate relief. Please arrive 10 minutes early to complete any necessary paperwork. We''ll see you soon!', 'text', 0.96, 'closing', NULL, NOW() - INTERVAL '1 day' + INTERVAL '5 seconds');

-- Insert Appointments
INSERT INTO appointments (business_id, customer_name, customer_phone, appointment_time, service_type, status, created_at, updated_at) VALUES
(1, 'Sarah Miller', '+1 (555) 234-5678', NOW() + INTERVAL '2 days', 'Dental Cleaning', 'scheduled', NOW() - INTERVAL '3 hours', NOW() - INTERVAL '3 hours'),
(1, 'John Davis', '+1 (555) 345-6789', NOW() + INTERVAL '5 days', 'Teeth Whitening Consultation', 'scheduled', NOW() - INTERVAL '6 hours', NOW() - INTERVAL '6 hours'),
(1, 'Emily Chen', '+1 (555) 456-7890', NOW() + INTERVAL '1 day', 'Dental Cleaning', 'scheduled', NOW() - INTERVAL '12 hours', NOW() - INTERVAL '12 hours'),
(1, 'Jessica Wilson', '+1 (555) 678-9012', NOW() - INTERVAL '1 day' + INTERVAL '4 hours', 'Emergency Dental Care', 'completed', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
(1, 'Lisa Anderson', '+1 (555) 901-2345', NOW() + INTERVAL '7 days', 'Invisalign Consultation', 'scheduled', NOW() - INTERVAL '4 days', NOW() - INTERVAL '4 days'),
(1, 'Amanda Garcia', '+1 (555) 890-1234', NOW() + INTERVAL '3 days', 'Dental Cleaning', 'scheduled', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days'),
(1, 'Christopher Taylor', '+1 (555) 123-4567', NOW() + INTERVAL '4 days', 'Dental Filling', 'scheduled', NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days');

-- Insert Integrations
INSERT INTO integrations (business_id, integration_type, name, status, configuration, created_at, updated_at) VALUES
(1, 'calendly', 'Calendly', 'connected', '{"calendar_url": "https://calendly.com/smilecare", "event_types": ["dental-cleaning", "consultation", "emergency"]}', NOW() - INTERVAL '1 month', NOW()),
(1, 'salesforce', 'Salesforce CRM', 'connected', '{"instance_url": "https://smilecare.my.salesforce.com", "contact_object": "Patient__c", "lead_object": "Lead"}', NOW() - INTERVAL '1 month', NOW()),
(1, 'twilio', 'Twilio', 'connected', '{"phone_number": "+1 (555) 100-2000", "webhook_url": "https://api.smilecare.com/webhook/twilio"}', NOW() - INTERVAL '6 months', NOW());

-- Output summary
SELECT 'Mock data insertion complete!' AS status;
SELECT COUNT(*) AS total_users FROM users;
SELECT COUNT(*) AS total_businesses FROM businesses;
SELECT COUNT(*) AS total_call_sessions FROM call_sessions;
SELECT COUNT(*) AS total_messages FROM conversation_messages;
SELECT COUNT(*) AS total_appointments FROM appointments;
SELECT COUNT(*) AS total_training_scenarios FROM ai_training_scenarios;
SELECT COUNT(*) AS total_integrations FROM integrations;