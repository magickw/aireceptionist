# Calendly Integration Architecture

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend (React/Next.js)"
        A[Calendly Page] --> B[API Client]
        C[Integrations Hub] --> B
    end
    
    subgraph "Backend (FastAPI)"
        D[Calendly Endpoints] --> E[Calendly Service]
        B --> D
    end
    
    subgraph "External Services"
        F[Calendly API]
        G[Calendly OAuth]
        H[Calendly Webhooks]
    end
    
    subgraph "Database"
        I[(calendar_integrations)]
        J[(appointments)]
    end
    
    E --> F
    E --> G
    E --> H
    E --> I
    H --> J
    
    style A fill:#61dafb,stroke:#333,stroke-width:2px
    style D fill:#4CAF50,stroke:#333,stroke-width:2px
    style E fill:#FF9800,stroke:#333,stroke-width:2px
    style F fill:#006BFF,stroke:#333,stroke-width:2px
```

## Component Flow

### 1. OAuth Connection Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant BE as Backend
    participant C as Calendly
    participant DB as Database
    
    U->>FE: Click "Connect Calendly"
    FE->>BE: GET /calendly/connect/calendly
    BE-->>FE: Return auth URL
    FE->>C: Redirect to Calendly OAuth
    U->>C: Authorize application
    C->>FE: Callback with code
    FE->>BE: POST /calendly/callback/calendly
    BE->>C: Exchange code for tokens
    C-->>BE: Return access & refresh tokens
    BE->>BE: Encrypt tokens
    BE->>DB: Store encrypted tokens
    BE-->>FE: Success response
    FE->>U: Show connected dashboard
```

### 2. Token Refresh Flow

```mermaid
sequenceDiagram
    participant BE as Backend
    participant C as Calendly
    participant DB as Database
    
    BE->>DB: Check token expiration
    alt Token expiring soon (< 30 min)
        BE->>C: POST /oauth/token (refresh grant)
        C-->>BE: New access & refresh tokens
        BE->>BE: Encrypt new tokens
        BE->>DB: Update tokens
    else Token still valid
        BE->>BE: Use existing token
    end
```

### 3. Webhook Event Flow

```mermaid
sequenceDiagram
    participant C as Calendly
    participant BE as Backend
    participant DB as Database
    participant FE as Frontend
    
    C->>BE: POST /calendly/webhooks/handler
    BE->>BE: Verify HMAC signature
    alt Valid signature
        BE->>BE: Parse event payload
        BE->>DB: Create/update appointment
        BE-->>C: 200 OK
        BE->>FE: Real-time update (optional)
    else Invalid signature
        BE-->>C: 401 Unauthorized
    end
```

### 4. Event Retrieval Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant BE as Backend
    participant C as Calendly
    participant DB as Database
    
    U->>FE: View Calendly page
    FE->>DB: Get integration record
    DB-->>FE: Return integration
    FE->>BE: GET /calendly/{id}/events
    BE->>DB: Get access token
    DB-->>BE: Return encrypted token
    BE->>BE: Decrypt token
    BE->>C: GET /scheduled_events
    C-->>BE: Return events list
    BE->>FE: Format and return events
    FE->>U: Display events in UI
```

## Data Models

### CalendarIntegration Table

```
┌─────────────────────────┐
│ calendar_integrations   │
├─────────────────────────┤
│ id (PK)                 │
│ business_id (FK)        │
│ provider = 'calendly'   │
│ access_token (encrypted)│
│ refresh_token (encrypted)│
│ token_expires_at        │
│ calendar_id (URI)       │
│ status                  │
│ last_sync_at            │
│ created_at              │
│ updated_at              │
└─────────────────────────┘
```

### Appointment Table (created from webhooks)

```
┌─────────────────────────┐
│ appointments            │
├─────────────────────────┤
│ id (PK)                 │
│ business_id (FK)        │
│ customer_id (FK)        │
│ customer_name           │
│ customer_phone          │
│ customer_email          │
│ appointment_time        │
│ service_type            │
│ status                  │
│ source = 'calendly'     │
│ created_at              │
│ updated_at              │
└─────────────────────────┘
```

## Security Architecture

```mermaid
graph LR
    A[User Browser] -->|HTTPS| B[Load Balancer]
    B --> C[Backend API]
    C --> D{Security Checks}
    D -->|OAuth State| E[CSRF Protection]
    D -->|Token Storage| F[AES-256 Encryption]
    D -->|Webhooks| G[HMAC-SHA256 Verification]
    E --> H[Calendly OAuth]
    F --> I[(Database)]
    G --> J[Calendly Webhooks]
    
    style D fill:#FF5722,stroke:#333,stroke-width:2px
    style F fill:#4CAF50,stroke:#333,stroke-width:2px
    style G fill:#2196F3,stroke:#333,stroke-width:2px
```

## API Request Flow

### Authenticated Request

```
Client Request
    ↓
[Authorization Header: Bearer {token}]
    ↓
[JWT Validation Middleware]
    ↓
[Business ID Extraction]
    ↓
[Calendly Endpoint Handler]
    ↓
[Service Layer]
    ↓
[Calendly API Call]
    ↓
[Response Formatting]
    ↓
Client Response
```

## Error Handling Strategy

```mermaid
graph TD
    A[API Call] --> B{Success?}
    B -->|Yes| C[Return Data]
    B -->|No| D{Error Type}
    
    D -->|401 Unauthorized| E[Refresh Token]
    E --> F[Retry Request]
    F --> G{Success?}
    G -->|Yes| C
    G -->|No| H[Reconnect Required]
    
    D -->|429 Rate Limit| I[Wait & Retry]
    I --> J[Exponential Backoff]
    J --> K[Max Retries?]
    K -->|No| F
    K -->|Yes| L[Error Response]
    
    D -->|Network Error| M[Log Error]
    M --> N[Error Response]
    
    style C fill:#4CAF50,stroke:#333
    style H fill:#F44336,stroke:#333
    style L fill:#FF9800,stroke:#333
    style N fill:#F44336,stroke:#333
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Client Side"
        A[React SPA]
    end
    
    subgraph "Edge/CDN"
        B[Vercel Edge Network]
    end
    
    subgraph "Backend"
        C[FastAPI App]
        D[Redis Cache]
    end
    
    subgraph "Data"
        E[(PostgreSQL)]
    end
    
    subgraph "External"
        F[Calendly API]
    end
    
    A --> B
    B --> C
    C --> D
    C --> E
    C --> F
    
    style F fill:#006BFF,stroke:#333,stroke-width:2px,color:#fff
```

## Technology Stack

```
Frontend
├── React 18
├── Next.js 14
├── TypeScript 5
├── Material-UI
└── Axios

Backend
├── Python 3.11
├── FastAPI
├── SQLAlchemy
├── aiohttp (async HTTP)
├── Cryptography (encryption)
└── Pydantic

External
├── Calendly API v2
├── Calendly OAuth 2.0
└── Calendly Webhooks

Database
└── PostgreSQL with pgvector
```

## Scalability Considerations

### Rate Limiting
- Calendly: 100 requests/minute per app
- Solution: Implement request queuing and caching

### Token Management
- Auto-refresh before expiry (30 min buffer)
- Queue pending requests during refresh

### Webhook Scaling
- Use message queue for high volume
- Async processing with background tasks
- Idempotent webhook handlers

### Database Optimization
```sql
-- Indexes for performance
CREATE INDEX idx_calendar_integrations_business 
ON calendar_integrations(business_id, provider);

CREATE INDEX idx_appointments_source 
ON appointments(source, business_id);
```

## Monitoring & Observability

```mermaid
graph LR
    A[Application] --> B[Metrics Collection]
    A --> C[Logging]
    A --> D[Error Tracking]
    
    B --> E[Prometheus/Grafana]
    C --> F[ELK Stack]
    D --> G[Sentry]
    
    E --> H[Dashboards]
    F --> I[Log Analysis]
    G --> J[Alerts]
    
    H --> K[Token Expiry Rates]
    H --> L[API Call Success Rates]
    H --> M[Webhook Delivery Rates]
    
    style A fill:#9C27B0,stroke:#333,color:#fff
    style E fill:#2196F3,stroke:#333,color:#fff
    style G fill:#F44336,stroke:#333,color:#fff
```

## Key Metrics to Track

1. **OAuth Metrics**
   - Connection success rate
   - Token refresh success rate
   - Average token lifetime

2. **API Metrics**
   - Requests per minute
   - Average response time
   - Error rate by endpoint

3. **Webhook Metrics**
   - Events received per hour
   - Processing success rate
   - Signature verification failures

4. **Business Metrics**
   - Active Calendly integrations
   - Bookings synced per day
   - Cancellation rate

---

This architecture ensures:
- ✅ **Security**: Multiple layers of protection
- ✅ **Scalability**: Handles growth gracefully
- ✅ **Reliability**: Robust error handling
- ✅ **Observability**: Comprehensive monitoring
- ✅ **Maintainability**: Clean separation of concerns
