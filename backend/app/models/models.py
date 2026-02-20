from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(Text, nullable=False)
    role = Column(String(50), default="business_owner") # admin, business_owner, staff
    status = Column(String(20), default="active") # active, inactive, suspended
    email_verified = Column(Boolean, default=False)
    phone = Column(String(20))
    avatar_url = Column(Text)
    password_changed_at = Column(DateTime)
    password_reset_token = Column(Text)
    password_reset_expires = Column(DateTime)
    last_login = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    businesses = relationship("Business", back_populates="owner")
    logs = relationship("SystemLog", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    settings = Column(JSON)
    phone = Column(String(20))
    address = Column(Text)
    website = Column(String(255))
    description = Column(Text)
    operating_hours = Column(JSON)
    business_license = Column(String(100))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="businesses")
    call_sessions = relationship("CallSession", back_populates="business")
    logs = relationship("SystemLog", back_populates="business")
    audit_logs = relationship("AuditLog", back_populates="business")
    customers = relationship("Customer", back_populates="business")
    integrations = relationship("Integration", back_populates="business")
    training_scenarios = relationship("AITrainingScenario", back_populates="business")
    appointments = relationship("Appointment", back_populates="business")
    menu_items = relationship("MenuItem", back_populates="business")
    orders = relationship("Order", back_populates="business")


class MenuItem(Base):
    """Menu items for restaurants and retail businesses"""
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2))
    unit = Column(String(50), default="per item")  # e.g., per item, per lb, per kg, per hour, per ton
    category = Column(String(100))  # e.g., Appetizers, Main Course, Drinks
    available = Column(Boolean, default=True)
    dietary_info = Column(JSON)  # e.g., {"vegetarian": true, "gluten_free": false}
    image_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="menu_items")
    order_items = relationship("OrderItem", back_populates="menu_item")


class Order(Base):
    """Customer orders for products/services"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    call_session_id = Column(String(100), ForeignKey("call_sessions.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))  # Link to Customer 360
    customer_name = Column(String(255))
    customer_phone = Column(String(20))
    status = Column(String(20), default="pending")  # pending, confirmed, preparing, ready, completed, cancelled
    total_amount = Column(DECIMAL(10, 2), default=0)
    notes = Column(Text)  # Special instructions
    confirmed_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="orders")
    call_session = relationship("CallSession", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Individual items within an order"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    item_name = Column(String(255), nullable=False)  # Snapshot of item name at time of order
    quantity = Column(Integer, default=1)
    unit_price = Column(DECIMAL(10, 2), nullable=False)  # Snapshot of price at time of order
    notes = Column(Text)  # Item-specific notes (e.g., "no onions")
    created_at = Column(DateTime, server_default=func.now())

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")


class CallSession(Base):
    __tablename__ = "call_sessions"

    id = Column(String(100), primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    customer_phone = Column(String(20))
    customer_name = Column(String(255))
    status = Column(String(20), default="active") # active, ended, transferred, voicemail
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer)
    ai_confidence = Column(DECIMAL(3, 2))
    summary = Column(Text)
    sentiment = Column(String(20)) # positive, neutral, negative
    language = Column(String(10), default="en") # en, es, fr, de, etc.
    detected_language = Column(String(10)) # Language detected from customer speech
    recording_url = Column(Text) # URL to stored recording
    recording_duration = Column(Integer) # Duration in seconds
    voicemail_detected = Column(Boolean, default=False)
    quality_score = Column(DECIMAL(5, 2)) # Call quality score 0-100
    satisfaction_prediction = Column(DECIMAL(3, 2)) # Predicted satisfaction 0-1
    customer_id = Column(Integer, ForeignKey("customers.id")) # Link to Customer 360
    created_at = Column(DateTime, server_default=func.now())

    business = relationship("Business", back_populates="call_sessions")
    messages = relationship("ConversationMessage", back_populates="session")
    orders = relationship("Order", back_populates="call_session")
    customer = relationship("Customer", back_populates="calls")


class Customer(Base):
    """Customer 360 view - unified customer profile"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    phone = Column(String(20), index=True)
    email = Column(String(255))
    name = Column(String(255))
    preferred_language = Column(String(10), default="en")
    
    # Engagement metrics
    total_calls = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    total_appointments = Column(Integer, default=0)
    total_spent = Column(DECIMAL(10, 2), default=0.0)
    
    # Satisfaction metrics
    avg_sentiment = Column(DECIMAL(3, 2))
    avg_quality_score = Column(DECIMAL(5, 2))
    last_satisfaction_prediction = Column(DECIMAL(3, 2))
    
    # Loyalty & Risk
    customer_since = Column(DateTime)
    last_interaction = Column(DateTime)
    loyalty_tier = Column(String(20), default="standard") # standard, silver, gold, platinum
    churn_risk = Column(DECIMAL(3, 2)) # 0-1, higher = more likely to churn
    is_vip = Column(Boolean, default=False)
    
    # Preferences
    preferred_contact_method = Column(String(20)) # phone, sms, email
    communication_preferences = Column(JSON)
    
    # Notes
    notes = Column(Text)
    tags = Column(JSON) # ["vip", "frequent_complainer", "prefers_morning"]
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    business = relationship("Business", back_populates="customers")
    calls = relationship("CallSession", back_populates="customer")
    appointments = relationship("Appointment", back_populates="customer")
    orders = relationship("Order", back_populates="customer")

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    call_session_id = Column(String(100), ForeignKey("call_sessions.id"))
    sender = Column(String(20), nullable=False) # customer, ai, agent
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text") # text, action, system
    confidence = Column(DECIMAL(3, 2))
    intent = Column(String(50))
    entities = Column(JSON)
    timestamp = Column(DateTime, server_default=func.now())

    session = relationship("CallSession", back_populates="messages")

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(10), nullable=False) # debug, info, warn, error
    message = Column(Text, nullable=False)
    service = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id"))
    business_id = Column(Integer, ForeignKey("businesses.id"))
    request_id = Column(String(100))
    metadata_ = Column("metadata", JSON)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="logs")
    business = relationship("Business", back_populates="logs")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    business_id = Column(Integer, ForeignKey("businesses.id"))
    operation = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="audit_logs")
    business = relationship("Business", back_populates="audit_logs")

class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    integration_type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    status = Column(String(20), default="disconnected") # connected, disconnected, error
    configuration = Column(JSON)
    credentials = Column(JSON)
    last_sync = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="integrations")

class AITrainingScenario(Base):
    __tablename__ = "ai_training_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    user_input = Column(Text, nullable=False)
    expected_response = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    success_rate = Column(DECIMAL(5, 2))
    last_tested = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="training_scenarios")

class TrainingSnapshot(Base):
    """A versioned snapshot of all active training scenarios for a business"""
    __tablename__ = "training_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    version = Column(Integer, default=1)
    name = Column(String(255))
    description = Column(Text)
    scenario_count = Column(Integer, default=0)
    avg_success_rate = Column(DECIMAL(5, 2))
    is_production = Column(Boolean, default=False)
    # Stores the scenario IDs that were part of this snapshot
    scenario_data = Column(JSON) 
    created_at = Column(DateTime, server_default=func.now())

    business = relationship("Business")

class BenchmarkResult(Base):
    """Results of a benchmark run against a snapshot or current scenarios"""
    __tablename__ = "benchmark_results"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    snapshot_id = Column(Integer, ForeignKey("training_snapshots.id"), nullable=True)
    total_scenarios = Column(Integer)
    passed_scenarios = Column(Integer)
    avg_score = Column(DECIMAL(5, 2))
    # Stores detailed pass/fail per scenario
    detailed_results = Column(JSON) 
    created_at = Column(DateTime, server_default=func.now())

    business = relationship("Business")
    snapshot = relationship("TrainingSnapshot")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))  # Link to Customer 360
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    service_type = Column(String(100))
    status = Column(String(20), default="scheduled") # scheduled, completed, cancelled, no_show
    no_show_probability = Column(DECIMAL(3, 2))  # Predicted no-show likelihood 0-1
    reminder_sent = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="appointments")
    customer = relationship("Customer", back_populates="appointments")


# Add pgvector to SQLAlchemy
from pgvector.sqlalchemy import Vector

class KnowledgeBaseDocument(Base):
    __tablename__ = "knowledge_base_documents"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending") # pending, indexing, complete, failed
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    business = relationship("Business") # Simplified relationship
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_base_documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536)) # Assuming Nova embedding size is 1536

    document = relationship("KnowledgeBaseDocument", back_populates="chunks")


class ApprovalRequest(Base):
    """Manager approval requests for AI actions requiring review"""
    __tablename__ = "approval_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    call_session_id = Column(String(100), ForeignKey("call_sessions.id"))
    request_type = Column(String(50))  # 'HUMAN_INTERVENTION', 'APPOINTMENT', 'PAYMENT', etc.
    status = Column(String(20), default="pending")  # pending, approved, rejected
    action_taken = Column(String(100))  # The action that was ultimately taken
    requested_by = Column(String(100))  # AI model name
    reason = Column(Text)  # Why approval was requested
    original_response = Column(Text)  # Original AI response
    final_response = Column(Text)  # Modified response after approval
    context = Column(JSON)  # Full context of the decision
    request_metadata = Column(JSON)  # Additional metadata
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    business = relationship("Business", backref="approval_requests")


class ManagerAction(Base):
    """Records manager actions on approval requests"""
    __tablename__ = "manager_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    approval_request_id = Column(Integer, ForeignKey("approval_requests.id"))
    manager_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50))  # 'approve', 'reject', 'modify'
    notes = Column(Text)
    timestamp = Column(DateTime, server_default=func.now())
    
    approval_request = relationship("ApprovalRequest", backref="manager_actions")
    manager = relationship("User")


class Webhook(Base):
    """Webhooks for real-time event notifications"""
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    events = Column(JSON, nullable=False) # List of events: call.completed, appointment.created, etc.
    secret = Column(String(255)) # Secret for signature verification
    status = Column(String(20), default="active") # active, paused, failed
    last_triggered_at = Column(DateTime)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    business = relationship("Business")


class CalendarIntegration(Base):
    """Calendar integrations for appointment sync"""
    __tablename__ = "calendar_integrations"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    provider = Column(String(50), nullable=False) # google, outlook, calendly
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    calendar_id = Column(String(255))
    status = Column(String(20), default="active") # active, expired, revoked
    last_sync_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    business = relationship("Business")


class SMSTemplate(Base):
    """SMS notification templates"""
    __tablename__ = "sms_templates"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    name = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False) # appointment.reminder, call.summary, etc.
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    business = relationship("Business")


class BusinessTemplate(Base):
    """Database-driven business type templates for AI agent configuration"""
    __tablename__ = "business_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_key = Column(String(50), unique=True, nullable=False, index=True)  # e.g., 'restaurant', 'medical'
    name = Column(String(255), nullable=False)  # Display name
    icon = Column(String(50))  # Material UI icon name
    description = Column(Text)
    autonomy_level = Column(String(20), nullable=False, default="MEDIUM")  # HIGH, MEDIUM, RESTRICTED
    
    # Risk profile
    high_risk_intents = Column(JSON)  # List of high-risk intents
    auto_escalate_threshold = Column(DECIMAL(3, 2), default=0.5)
    confidence_threshold = Column(DECIMAL(3, 2), default=0.6)
    
    # Common intents for this business type
    common_intents = Column(JSON)
    
    # Field definitions for data collection
    fields = Column(JSON)  # Dict of field_name -> {required, validation, prompt, for_intents}
    
    # Booking/order flow configuration
    booking_flow = Column(JSON)  # {type, steps, final_action, confirmation_message}
    
    # AI prompts
    system_prompt_addition = Column(Text)
    example_responses = Column(JSON)
    
    # Versioning and status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Default template for new businesses
    version = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    versions = relationship("TemplateVersion", back_populates="template", cascade="all, delete-orphan")
    creator = relationship("User")


class TemplateVersion(Base):
    """Version history for business templates to enable A/B testing and rollbacks"""
    __tablename__ = "template_versions"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("business_templates.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    
    # Snapshot of template configuration at this version
    name = Column(String(255))
    icon = Column(String(50))
    description = Column(Text)
    autonomy_level = Column(String(20))
    high_risk_intents = Column(JSON)
    auto_escalate_threshold = Column(DECIMAL(3, 2))
    confidence_threshold = Column(DECIMAL(3, 2))
    common_intents = Column(JSON)
    fields = Column(JSON)
    booking_flow = Column(JSON)
    system_prompt_addition = Column(Text)
    example_responses = Column(JSON)
    
    # Version metadata
    change_description = Column(Text)  # Description of what changed
    is_active = Column(Boolean, default=False)  # Currently in production
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    template = relationship("BusinessTemplate", back_populates="versions")
    creator = relationship("User")


class IntentClassification(Base):
    """Training data and model for intent classification"""
    __tablename__ = "intent_classifications"

    id = Column(Integer, primary_key=True, index=True)
    business_type = Column(String(50), nullable=False)  # e.g., 'restaurant', 'medical'
    intent = Column(String(100), nullable=False)  # e.g., 'make_reservation', 'order_food'
    user_input = Column(Text, nullable=False)  # Example user utterance
    entities = Column(JSON)  # Extracted entities from this example
    confidence = Column(DECIMAL(3, 2))  # Expected confidence score
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class BusinessTypeSuggestion(Base):
    """NLP-based business type detection from description"""
    __tablename__ = "business_type_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    business_type = Column(String(50), nullable=False)
    keywords = Column(JSON)  # Keywords that indicate this business type
    phrases = Column(JSON)  # Common phrases for this business type
    confidence_weight = Column(DECIMAL(3, 2), default=1.0)  # Weight for scoring
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
