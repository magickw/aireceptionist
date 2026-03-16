# Receptium — AI-Orchestrated Business Operations Platform

Receptium is an AI-native operating layer for businesses, powered by the **Amazon Nova** model family. It handles real-time voice reception, autonomous workflow execution, and predictive customer intelligence — built for the **Amazon Nova Hackathon**.

---

## How It Works

Receptium uses a **Stream-Reason-Execute** architecture across three layers:

```
Customer Call
     │
     ▼
┌─────────────────────────────────────────────┐
│  Voice Layer  (nova_sonic_stream.py)         │
│  Browser STT → WebSocket → Polly TTS        │
│  Thinking-block filter · Sentiment SSML     │
│  Incremental TTS · Conversational fillers   │
└──────────────────┬──────────────────────────┘
                   │ transcript
                   ▼
┌─────────────────────────────────────────────┐
│  Reasoning Layer  (nova_reasoning.py)        │
│  Layer 1: Deterministic safety triggers     │
│  Layer 2: Nova Lite intent + entity extract │
│  Layer 3: Industry-specific governance      │
│  Layer 4: Approval workflow for high-risk   │
└──────────────────┬──────────────────────────┘
                   │ action + entities
                   ▼
┌─────────────────────────────────────────────┐
│  Execution Layer  (action_execution_service) │
│  Appointments · Orders · CRM · Payments     │
│  Workflow orchestration · Memory recall     │
└─────────────────────────────────────────────┘
```

---

## Nova Model Usage

| Model | Role | Where |
|---|---|---|
| **Nova Lite** | Intent classification, entity extraction, reasoning, behavioral analysis | `nova_reasoning.py`, `customer_intelligence.py`, `nova_act.py` |
| **Nova Sonic** (model ID reserved) | Voice model identifier; actual voice pipeline uses Transcribe STT + Nova Lite + Polly TTS | `nova_sonic.py`, `nova_sonic_stream.py` |
| **Nova Act** | Autonomous browser automation (Calendly, Salesforce, HubSpot) via Playwright | `nova_act.py` |
| **Titan Embeddings** | Vector embeddings for semantic customer history search (pgvector) | `customer_intelligence.py` |

> **Voice architecture note:** The real-time voice pipeline uses browser Web Speech API or Amazon Transcribe for STT, Nova Lite for reasoning via `converse_stream`, and Amazon Polly Neural for TTS. The `NovaSonicStreamSession` manages the full bidirectional session lifecycle.

---

## Key Features

### Real-Time Voice Reception
- WebSocket-based bidirectional audio streaming
- Amazon Transcribe Streaming (no S3 required) with S3-batch fallback
- Incremental sentence-level TTS for sub-150ms perceived latency
- Thinking-block filtering — internal reasoning tokens never reach the user
- Sentiment-aware SSML (soft tone for negative sentiment, cheerful for positive)
- Conversational fillers during processing delays
- Automatic language detection and mid-session language switching (10 languages)

### 4-Layer Governance Engine
- **Layer 1 — Deterministic triggers:** Critical keywords (911, lawsuit, gas leak), VIP + negative sentiment, industry-specific emergencies — bypass the model entirely
- **Layer 2 — Nova Lite reasoning:** Intent classification (15+ intents), entity extraction, confidence scoring, escalation risk
- **Layer 3 — Combined governance:** Industry-specific confidence and risk thresholds (Medical: 0.85, Restaurant: 0.60), high-risk intent detection, intent validation
- **Layer 4 — Approval workflow:** Human review queue for high-risk actions, manager notification, pending approval tracking

### Autonomous Action Execution
- `bookAppointment` — calendar conflict detection, no-show risk scoring, operating hours validation
- `placeOrder` / `confirmOrder` — cart accumulation with item merging, subtotal tracking, DB persistence via `OrderService`
- `checkAvailability` — Google/Microsoft/Calendly calendar integration with smart scheduling alternatives
- `transferToHuman`, `processPayment`, `sendDirections`, `sendConfirmationSMS`
- `recallCustomerMemory` — per-customer persistent memory store
- `executeWorkflow` — atomic multi-step workflows (`bookingWorkflow`, `orderWorkflow`) with rollback compensation

### Nova Act Browser Automation
- Real Playwright browser automation for Calendly booking, Salesforce, and HubSpot CRM updates
- Nova Lite multimodal screenshot verification after each step
- `CognitiveAutomationEngine` — dynamic workflow generation, self-healing on failure, performance optimization, adaptive learning from execution history

### Customer 360 Intelligence
- Unified customer profiles: calls, orders, appointments, sentiment, loyalty tier
- LTV projection including both order revenue and appointment revenue, churn-adjusted
- Churn risk scoring via `CustomerIntelligenceService` (single source of truth — `ChurnService` delegates to it)
- pgvector semantic search across full customer interaction history (Titan Embeddings)
- VIP identification with PLATINUM / GOLD / SILVER / BRONZE tiers
- Behavioral pattern analysis and next-best-action recommendations via Nova Lite
- Real-time customer score during live calls

### Multimodal Support
- Image upload: base64 encoding + Nova Lite analysis prompt
- PDF extraction via `pypdf` / `PyPDF2`
- Word document extraction via `python-docx`
- Graceful fallback messages if extraction libraries are not installed

### Additional Capabilities
- **40+ REST API endpoints** across auth, businesses, voice, orders, appointments, analytics, campaigns, payments, CRM, knowledge base, smart scheduling, and more
- **Outbound campaigns** with scheduler, concurrent call management, and retry logic
- **Knowledge base** with RAG context injection into reasoning prompts
- **AI training scenarios** — few-shot examples per business, synthetic data generation via Nova Lite
- **Smart scheduling** — no-show probability prediction, optimal time suggestions
- **Revenue analytics, forecasting, sentiment analysis, call summaries**
- **Multi-language support** — 10 languages with cultural adaptation guidelines
- **Rate limiting, security headers, request logging, JWT auth with refresh tokens**

---

## Architecture

```
aireceptionist/
├── backend/                    # FastAPI (Python 3.10+)
│   ├── app/
│   │   ├── api/v1/endpoints/   # 40+ REST + WebSocket endpoints
│   │   ├── core/
│   │   │   ├── agent.py        # Lightweight single-turn agent (business-context-driven)
│   │   │   ├── config.py       # Centralized settings (model IDs, feature flags)
│   │   │   └── security.py     # JWT, rate limiting, security headers
│   │   ├── models/models.py    # SQLAlchemy ORM (PostgreSQL + pgvector)
│   │   ├── services/
│   │   │   ├── nova_sonic_stream.py      # Real-time voice session manager
│   │   │   ├── nova_sonic.py             # Batch STT→Reason→TTS fallback pipeline
│   │   │   ├── nova_reasoning.py         # 4-layer governance + Nova Lite reasoning
│   │   │   ├── nova_act.py               # Browser automation + CognitiveAutomationEngine
│   │   │   ├── action_execution_service.py # Tool dispatcher (appointments, orders, etc.)
│   │   │   ├── customer_intelligence.py  # Embeddings, churn, VIP, behavioral analysis
│   │   │   ├── customer_360_service.py   # Unified customer profiles + LTV
│   │   │   ├── churn_service.py          # Delegates to CustomerIntelligenceService
│   │   │   ├── multimodal_service.py     # Image + document processing
│   │   │   ├── order_service.py          # Order lifecycle + status notifications
│   │   │   ├── calendar_service.py       # Google / Microsoft / Calendly integration
│   │   │   ├── knowledge_base.py         # RAG context retrieval
│   │   │   ├── workflow_engine.py        # Atomic multi-step workflow execution
│   │   │   └── smart_scheduling_service.py # No-show prediction, optimal times
│   │   └── main.py             # FastAPI app, CORS, middleware, startup migrations
│   ├── .env.example            # Template — copy to .env and fill in values
│   └── requirements.txt
├── frontend/                   # Next.js
└── database/                   # Schema migrations
```

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL with `pgvector` extension
- AWS account with Bedrock access (Nova Lite, Titan Embeddings enabled)
- Twilio account (for voice/SMS)

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Copy the template and fill in your values
cp .env.example .env

uvicorn app.main:app --reload
```

The server starts on `http://localhost:8000`. Interactive API docs at `/api/openapi.json`.

On first startup, the app automatically creates any missing database tables and columns (refresh tokens, campaigns, account lockout fields).

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_BACKEND_URL
npm run dev
```

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and set:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (supports pgvector) |
| `SECRET_KEY` | App secret for session signing |
| `JWT_SECRET` | JWT signing secret (min 32 chars) |
| `AWS_ACCESS_KEY_ID` | AWS credentials for Bedrock, Transcribe, Polly |
| `AWS_SECRET_ACCESS_KEY` | |
| `AWS_REGION` | Default: `us-east-1` |
| `TWILIO_ACCOUNT_SID` | Twilio credentials for voice/SMS |
| `TWILIO_AUTH_TOKEN` | |
| `TWILIO_PHONE_NUMBER` | |
| `REDIS_URL` | Optional — for caching |

**Never commit `.env` to version control.** The `.gitignore` excludes it.

### Optional Python Dependencies

For full document extraction support:

```bash
pip install pypdf python-docx          # PDF and Word document extraction
pip install amazon-transcribe          # Streaming STT (no S3 required)
```

---

## Configuration

Model IDs and feature flags are centralized in `app/core/config.py` and can be overridden via environment variables:

| Setting | Default | Description |
|---|---|---|
| `BEDROCK_REASONING_MODEL` | `amazon.nova-lite-v1:0` | Nova Lite for reasoning |
| `BEDROCK_VOICE_MODEL` | `amazon.nova-sonic-v1:0` | Voice model identifier |
| `BEDROCK_AUTOMATION_MODEL` | `amazon.nova-act-v1:0` | Browser automation |
| `BEDROCK_EMBEDDING_MODEL` | `amazon.titan-embed-text-v1` | Vector embeddings |
| `STREAMING_STT_ENABLED` | `true` | Use Transcribe Streaming (no S3) |
| `INCREMENTAL_TTS_ENABLED` | `true` | Sentence-level TTS for lower latency |
| `TTS_MIN_SENTENCE_LENGTH` | `20` | Min chars before synthesizing a sentence |
| `NOVA_SONIC_STREAMING_ENABLED` | `true` | Enable streaming voice sessions |

---

## API Overview

Base path: `/api`

| Tag | Endpoints | Description |
|---|---|---|
| `voice` | `WS /voice/stream/{id}`, `POST /voice/session` | Real-time voice WebSocket + HTTP fallback |
| `businesses` | CRUD `/businesses` | Business profiles, settings, types |
| `appointments` | CRUD `/appointments` | Appointment management |
| `orders` | CRUD `/orders` | Order lifecycle + status updates |
| `customers` | `/customers/{phone}` | Customer 360 profiles |
| `customer-intelligence` | `/customer-intelligence/*` | Churn, VIP, behavioral analysis |
| `analytics` | `/analytics/*` | Call analytics, sentiment trends |
| `campaigns` | `/campaigns/*` | Outbound campaign management |
| `knowledge-base` | `/knowledge-base/*` | RAG document management |
| `calendar` | `/calendar/*` | Google / Microsoft / Calendly OAuth + booking |
| `automation` | `/automation/*` | Nova Act workflow execution |
| `ai-training` | `/ai-training/*` | Training scenarios, synthetic data |
| `smart-scheduling` | `/smart-scheduling/*` | No-show prediction, optimal times |
| `payments` | `/payments/*` | Payment processing |
| `integrations` | `/integrations/*` | POS, CRM, calendar integrations |

Full interactive docs: `GET /api/openapi.json`

---

## Governance Tiers

| Tier | Condition | Behavior |
|---|---|---|
| `AUTO` | High confidence, low risk, no high-risk intent | Executes immediately |
| `CONFIRM` | Medium confidence | Asks customer to confirm before acting |
| `PRIORITY` | VIP customer | Expedited handling |
| `HUMAN_REVIEW` | Low confidence / high risk / high-risk intent | Pauses for human approval |
| `ESCALATE` | Deterministic trigger (emergency, legal, safety) | Immediate transfer, bypasses model |

Industry risk profiles (confidence threshold / auto-escalate threshold):

| Industry | Confidence | Escalate | High-Risk Intents |
|---|---|---|---|
| Restaurant | 0.60 | 0.70 | food_poisoning, severe_allergy |
| Medical / Dental | 0.85 | 0.40 | medical_emergency, chest_pain |
| Law Firm | 0.80 | 0.50 | legal_action, lawsuit |
| HVAC / Plumbing | 0.65 | 0.60 | gas_leak, carbon_monoxide |
| Hotel | 0.70 | 0.50 | security_issue, emergency |
| Salon / Spa | 0.60 | 0.70 | allergic_reaction |
| Retail | 0.60 | 0.70 | product_issue, return_dispute |

---

## Submission Details

- **Hackathon:** AWS Amazon Nova Hackathon — February 2026
- **Category:** Agentic AI / Voice AI
- **Models:** Nova Lite, Nova Sonic (model ID), Nova Act, Titan Embeddings
- **Focus:** Autonomous Business Operations
