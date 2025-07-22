-- Enhanced database schema with authentication and logging

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role VARCHAR(50) DEFAULT 'business_owner' CHECK (role IN ('admin', 'business_owner', 'staff')),
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
  email_verified BOOLEAN DEFAULT FALSE,
  phone VARCHAR(20),
  avatar_url TEXT,
  password_changed_at TIMESTAMP,
  password_reset_token TEXT,
  password_reset_expires TIMESTAMP,
  last_login TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update businesses table to link with users
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS website VARCHAR(255);
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Call sessions table for WebSocket calls
CREATE TABLE IF NOT EXISTS call_sessions (
  id VARCHAR(100) PRIMARY KEY,
  business_id INTEGER REFERENCES businesses(id),
  customer_phone VARCHAR(20),
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'ended', 'transferred')),
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP,
  duration_seconds INTEGER,
  ai_confidence DECIMAL(3,2),
  summary TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation messages for call tracking
CREATE TABLE IF NOT EXISTS conversation_messages (
  id SERIAL PRIMARY KEY,
  call_session_id VARCHAR(100) REFERENCES call_sessions(id),
  sender VARCHAR(20) NOT NULL CHECK (sender IN ('customer', 'ai', 'agent')),
  content TEXT NOT NULL,
  message_type VARCHAR(20) DEFAULT 'text' CHECK (message_type IN ('text', 'action', 'system')),
  confidence DECIMAL(3,2),
  intent VARCHAR(50),
  entities JSONB,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System logs table
CREATE TABLE IF NOT EXISTS system_logs (
  id SERIAL PRIMARY KEY,
  level VARCHAR(10) NOT NULL CHECK (level IN ('debug', 'info', 'warn', 'error')),
  message TEXT NOT NULL,
  service VARCHAR(50),
  user_id INTEGER REFERENCES users(id),
  business_id INTEGER REFERENCES businesses(id),
  request_id VARCHAR(100),
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Business operations audit log
CREATE TABLE IF NOT EXISTS audit_logs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  business_id INTEGER REFERENCES businesses(id),
  operation VARCHAR(100) NOT NULL,
  resource_type VARCHAR(50),
  resource_id VARCHAR(100),
  old_values JSONB,
  new_values JSONB,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Integration configurations
CREATE TABLE IF NOT EXISTS integrations (
  id SERIAL PRIMARY KEY,
  business_id INTEGER REFERENCES businesses(id),
  integration_type VARCHAR(50) NOT NULL,
  name VARCHAR(100) NOT NULL,
  status VARCHAR(20) DEFAULT 'disconnected' CHECK (status IN ('connected', 'disconnected', 'error')),
  configuration JSONB,
  credentials JSONB, -- Store encrypted credentials
  last_sync TIMESTAMP,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI training data and scenarios
CREATE TABLE IF NOT EXISTS ai_training_scenarios (
  id SERIAL PRIMARY KEY,
  business_id INTEGER REFERENCES businesses(id),
  title VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(50),
  user_input TEXT NOT NULL,
  expected_response TEXT NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  success_rate DECIMAL(5,2),
  last_tested TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_businesses_user_id ON businesses(user_id);
CREATE INDEX IF NOT EXISTS idx_call_sessions_business_id ON call_sessions(business_id);
CREATE INDEX IF NOT EXISTS idx_call_sessions_started_at ON call_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_call_session_id ON conversation_messages(call_session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_timestamp ON conversation_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_business_id ON audit_logs(business_id);
CREATE INDEX IF NOT EXISTS idx_integrations_business_id ON integrations(business_id);

-- Create default admin user (password: admin123456)
INSERT INTO users (name, email, password, role, email_verified) 
VALUES (
  'System Administrator', 
  'admin@ai-receptionist.com', 
  '$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3pc0mzFO3y', -- bcrypt hash of 'admin123456'
  'admin', 
  TRUE
) ON CONFLICT (email) DO NOTHING;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_businesses_updated_at BEFORE UPDATE ON businesses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_integrations_updated_at BEFORE UPDATE ON integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ai_training_scenarios_updated_at BEFORE UPDATE ON ai_training_scenarios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();