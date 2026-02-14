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
    status = Column(String(20), default="active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="businesses")
    call_sessions = relationship("CallSession", back_populates="business")
    logs = relationship("SystemLog", back_populates="business")
    audit_logs = relationship("AuditLog", back_populates="business")
    integrations = relationship("Integration", back_populates="business")
    training_scenarios = relationship("AITrainingScenario", back_populates="business")
    appointments = relationship("Appointment", back_populates="business")

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
    recording_url = Column(Text) # URL to stored recording
    recording_duration = Column(Integer) # Duration in seconds
    voicemail_detected = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    business = relationship("Business", back_populates="call_sessions")
    messages = relationship("ConversationMessage", back_populates="session")

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

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    service_type = Column(String(100))
    status = Column(String(20), default="scheduled") # scheduled, completed, cancelled, no_show
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="appointments")


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
