# Receptium: AI-Orchestrated Business Operations Platform (AIBOP)

**Receptium** is an **AI-native operating layer** that sits on top of business infrastructure—powered by models like **Amazon Nova Sonic** and **Nova Lite**.

It is **not** a chatbot.
It is **not** a CRM plugin.
It is an intelligent execution engine that unifies:
- **Real-Time Voice Reception** (Speech-to-Speech)
- **Deterministic Workflow Execution** (Scheduling, Orders, CRM Sync)
- **Predictive Customer Intelligence** (Churn Risk, LTV Analysis)

Built for the **Amazon Nova Hackathon**.

## 🚀 The Nova Advantage

This platform demonstrates the full power of the Amazon Nova model family working in concert:

*   **Nova 2 Sonic:** Low-latency conversational voice AI (Speech-to-Speech integration) for natural, interruptible dialogue.
*   **Nova 2 Lite:** High-confidence structured reasoning for autonomous decision making and intent classification.
*   **Nova Act:** Autonomous UI automation for executing real-world workflows (Calendly, CRM, etc.).
*   **Nova Embeddings:** Multimodal embeddings for advanced customer intelligence and RAG.

## 🏗 Architecture & Strategic Positioning

Receptium utilizes a **Stream-Reason-Execute** architecture designed for enterprise reliability.

### 1. Real-Time Voice Engine (Streaming)
- **Sub-150ms Latency:** Optimized bidirectional audio streaming.
- **Thinking Block Filter:** Automatically strips internal reasoning tokens from the audio stream, ensuring the user hears only the final response.

### 2. Context-Aware Orchestration
- **Dynamic Prompting:** System prompts are compiled at runtime using Customer 360 data, business state (e.g., "inventory level"), and RAG knowledge.
- **Deterministic Execution:** AI extracts *intent* and *parameters*, but code handles the *execution*, preventing hallucinations.

### 3. Customer 360 "Data Moat"
- **Unified Profile:** Aggregates calls, orders, appointments, and sentiment scores.
- **Predictive Analytics:** Uses historical data to predict churn risk and identify VIPs.

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
