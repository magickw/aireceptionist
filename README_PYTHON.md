# AI Receptionist Pro (Python/FastAPI Backend)

This is the enhanced version of the AI Receptionist using Python (FastAPI) and Amazon Nova models.

## 🚀 Setup

### Backend (Python)

1. Navigate to `backend_python`:
   ```bash
   cd backend_python
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure `.env`:
   Copy `.env.example` to `.env` and fill in your details (Database URL, AWS Credentials, Twilio).

5. Run the server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend (Next.js)

1. Navigate to `frontend`:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Update `.env.local`:
   Ensure `NEXT_PUBLIC_API_URL` points to `http://localhost:8000/api/v1`.

4. Run the frontend:
   ```bash
   npm run dev
   ```

## 🏗 Architecture

- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL (SQLAlchemy ORM)
- **AI Models:** Amazon Nova (Bedrock), Polly (TTS)
- **Voice:** Twilio Media Streams (WebSocket)
- **Frontend:** Next.js

## 📝 Features

- **Authentication:** JWT (OAuth2 compatible)
- **Business Management:** CRUD for businesses
- **Call Logs:** Real-time logging of calls
- **Analytics:** Dashboard metrics (Mocked for demo)
- **Voice Agent:** Autonomous AI receptionist using Amazon Nova Lite
