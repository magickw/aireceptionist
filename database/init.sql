CREATE TABLE IF NOT EXISTS businesses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- e.g., 'restaurant', 'spa', 'salon'
    settings JSONB
);

CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    business_id INTEGER REFERENCES businesses(id),
    customer_name VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(50) NOT NULL,
    appointment_time TIMESTAMP WITH TIME ZONE NOT NULL,
    service_type VARCHAR(255),
    status VARCHAR(50) DEFAULT 'confirmed', -- e.g., 'confirmed', 'cancelled'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS call_logs (
    id SERIAL PRIMARY KEY,
    business_id INTEGER REFERENCES businesses(id),
    customer_phone VARCHAR(50) NOT NULL,
    call_sid VARCHAR(255), -- from Twilio or other provider
    transcript TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
