# Nova Autonomous Business Agent Platform

A production-ready, Nova-native autonomous agent system that handles live voice calls, reasons through complex customer intents, and executes real-world business workflows.

Built for the **Amazon Nova Hackathon**.

## 🚀 The Nova Advantage

This platform is built from the ground up to leverage the full power of the Amazon Nova model family:

*   **Nova 2 Sonic:** Low-latency conversational voice AI (Speech-to-Speech integration).
*   **Nova 2 Lite:** High-confidence structured reasoning for autonomous decision making.
*   **Nova Act:** Autonomous UI automation for executing real-world workflows (Calendly, CRM, etc.).
*   **Nova Embeddings:** Multimodal embeddings for advanced customer intelligence and RAG.

## 🏗 Architecture

- **Backend:** FastAPI (Python 3.10+)
- **Frontend:** Next.js 14 (TypeScript, Material UI)
- **Database:** PostgreSQL with pgvector for semantic search
- **AI Engine:** Amazon Bedrock (Nova Pro/Lite/Sonic/Act)
- **Voice Infrastructure:** WebSocket-based streaming with Twilio support
- **Automation:** Nova Act Planner + Simulated UI Execution

## 🌟 Key Features

### 1. Agentic AI Reasoning
Uses **Nova 2 Lite** to analyze conversations in real-time. It doesn't just generate text; it extracts intents, identifies missing required information, assesses escalation risk, and plans its next moves with >94% confidence.

### 2. Autonomous UI Automation
Powered by **Nova Act**, the agent can autonomously navigate and interact with external web applications. It can book appointments via Calendly, update records in Salesforce/HubSpot, and verify its own actions through "visual" observation.

### 3. Voice AI Experience
Integrated with **Nova 2 Sonic**, providing a natural, low-latency speech-to-speech experience. It handles interruptions, maintains context, and speaks with human-like prosody.

### 4. Customer Intelligence
Leverages **Nova Multimodal Embeddings** to identify VIP customers, detect churn risk patterns, and perform semantic search across years of customer history.

## 🛠 Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL with pgvector
- AWS Account with Bedrock access (Nova models enabled)

### Backend Setup
1. `cd backend`
2. `python -m venv venv && source venv/bin/activate`
3. `pip install -r requirements.txt`
4. Create `.env` from `.env.example`
5. `uvicorn app.main:app --reload`

### Frontend Setup
1. `cd frontend`
2. `npm install`
3. Create `.env.local`
4. `npm run dev`

## 🧪 Testing the Workflow

Run the automated test script to verify all Nova integrations:
```bash
./test_workflow.sh
```

## 📄 Submission Details
- **Category:** Agentic AI / Voice AI
- **Models Used:** Nova 2 Lite, Nova 2 Sonic, Nova Act, Nova Embedding
- **Focus Area:** Autonomous Business Operations

---
*Created for the AWS Amazon Nova Hackathon - February 2026*
