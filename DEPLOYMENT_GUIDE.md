# Deployment Guide

## Overview

This project uses a **separate deployment strategy**:
- **Backend**: Python/FastAPI → Deploy on **Render**
- **Frontend**: Next.js → Deploy on **Vercel**

---

## Step 1: Deploy Backend on Render

### Option A: Using render.yaml (Recommended)

1. **Push your code to GitHub** (if not already done)
2. **Go to Render Dashboard**: https://dashboard.render.com
3. **Click "New +" → "Web Service"**
4. **Connect your GitHub repository**
5. **Select the branch**: `main`
6. **Render will detect the `render.yaml` file** and configure automatically
7. **Review settings**:
   - Name: `receptium`
   - Region: Oregon (or closest to you)
   - Branch: `main`
   - Runtime: Python 3.10
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
8. **Click "Create Web Service"**

### Option B: Manual Configuration

1. Go to Render Dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `receptium`
   - **Environment**: `Python`
   - **Region**: Oregon
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Click "Advanced"
6. Add Environment Variables (see below)
7. Click "Create Web Service"

### Environment Variables for Backend

Add these in Render → Your Service → Environment:

```
SECRET_KEY=your-secret-key-here
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number
NEXT_PUBLIC_FRONTEND_URL=https://your-vercel-app.vercel.app
```

### PostgreSQL Database

1. In Render, click "New +" → "PostgreSQL"
2. Name: `aireceptionist-db`
3. Database: `aireceptionist`
4. User: `aireceptionist`
5. Plan: Free (or paid)
6. Click "Create Database"
7. **Important**: After creation, click the database → Connect → Internal Database URL
8. Copy the connection string and add it as `DATABASE_URL` environment variable in your backend service

### Load Mock Data (Optional)

After deployment, connect to your PostgreSQL database:

```bash
# Get the internal database URL from Render
# Connect using psql
psql $DATABASE_URL

# Or use Render's built-in shell:
# Go to your database → Shell

# Run the mock data script
\i https://raw.githubusercontent.com/magickw/aireceptionist/main/database/mock_data.sql
```

---

## Step 2: Deploy Frontend on Vercel

### Using Vercel CLI (Recommended)

1. **Install Vercel CLI**:
```bash
npm install -g vercel
```

2. **Deploy frontend**:
```bash
cd frontend
vercel
```

3. **Follow the prompts**:
   - Set up and continue (if new project)
   - Link to existing project (if already deployed)
   - Project name: `aireceptionist-frontend`
   - Directory: `./` (already in frontend folder)
   - Override settings? No

### Using Vercel Dashboard

1. Go to Vercel: https://vercel.com/dashboard
2. Click "Add New Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`
5. Add Environment Variables:
   - `NEXT_PUBLIC_BACKEND_URL`: Your Render backend URL (e.g., `https://receptium.onrender.com`)
   - `NEXT_PUBLIC_WS_URL`: Your WebSocket URL (e.g., `wss://receptium.onrender.com/api/v1/voice/ws`)
6. Click "Deploy"

### Update CORS in Backend

After deploying, update your backend CORS settings to allow your Vercel frontend:

In `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-vercel-app.vercel.app"],  # Add your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Step 3: Configure DNS (Optional)

If you have custom domains:

### Backend (Render)
1. Go to your backend service in Render
2. Settings → Custom Domains
3. Add your domain (e.g., `api.yourdomain.com`)
4. Follow DNS instructions

### Frontend (Vercel)
1. Go to your project in Vercel
2. Settings → Domains
3. Add your domain (e.g., `www.yourdomain.com`)
4. Follow DNS instructions

---

## Step 4: Verify Deployment

### Test Backend
```bash
curl https://receptium.onrender.com/health
```

Should return:
```json
{"status": "healthy"}
```

### Test Frontend
Open your Vercel URL in browser: `https://your-vercel-app.vercel.app`

### Test WebSocket Connection
Open browser console and check:
- WebSocket connection should connect to `wss://receptium.onrender.com/api/v1/voice/ws`
- No CORS errors

---

## Common Issues & Solutions

### Issue: "Application exited early" on Render

**Cause**: Render is trying to run the root `package.json` start command

**Solution**: 
- Use the `render.yaml` file I created
- Or manually configure root directory as `backend`
- Or change build command to `cd backend && pip install -r requirements.txt`
- And start command to `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Issue: CORS Errors

**Cause**: Frontend URL not in CORS allowlist

**Solution**: Update `backend/app/main.py` to include your Vercel URL:
```python
allow_origins=["https://your-vercel-app.vercel.app"]
```

### Issue: WebSocket Connection Failed

**Cause**: WebSocket URL not using `wss://` protocol

**Solution**: Ensure frontend uses:
```javascript
const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'wss://receptium.onrender.com/api/v1/voice/ws';
```

### Issue: Database Connection Failed

**Cause**: DATABASE_URL not set correctly

**Solution**: 
1. Go to Render database → Connect
2. Copy Internal Database URL
3. Add to backend service environment variables as `DATABASE_URL`

### Issue: Build Timeout on Render

**Cause**: Build taking too long

**Solution**: 
- Use `requirements.txt` instead of `poetry.lock`
- Remove unnecessary dependencies
- Increase build timeout in Render settings

---

## Production Checklist

### Backend (Render)
- [ ] PostgreSQL database created
- [ ] DATABASE_URL environment variable set
- [ ] SECRET_KEY environment variable set
- [ ] AWS credentials set (for Nova models)
- [ ] Twilio credentials set (for voice)
- [ ] CORS configured for Vercel frontend
- [ ] Health endpoint accessible
- [ ] WebSocket endpoint accessible

### Frontend (Vercel)
- [ ] NEXT_PUBLIC_BACKEND_URL set
- [ ] NEXT_PUBLIC_WS_URL set
- [ ] Build successful
- [ ] All pages accessible
- [ ] API calls working
- [ ] WebSocket connection working

### Testing
- [ ] Health check passes
- [ ] Login works
- [ ] Dashboard loads
- [ ] Call simulator works
- [ ] Analytics displays data
- [ ] Customer intelligence works

---

## Monitoring

### Backend (Render)
- Go to Dashboard → Your Service
- View logs, metrics, and events
- Set up alerts for errors or high response time

### Frontend (Vercel)
- Go to Dashboard → Your Project
- View logs, analytics, and deployments
- Set up webhooks for deployment notifications

---

## Cost Estimate

### Render (Backend + Database)
- **Web Service**: $0 (Free) or $7/month (Starter)
- **PostgreSQL**: $0 (Free) or $7/month (Starter)
- **Total**: $0-$14/month

### Vercel (Frontend)
- **Hobby**: Free (with Vercel branding)
- **Pro**: $20/month (remove branding, analytics)
- **Total**: $0-$20/month

### Total Monthly Cost: $0-$34/month

---

## Support

### Render Documentation
- https://render.com/docs

### Vercel Documentation
- https://vercel.com/docs

### Amazon Nova Documentation
- https://docs.aws.amazon.com/bedrock/

---

## Next Steps

1. **Deploy backend** on Render using `render.yaml`
2. **Deploy frontend** on Vercel
3. **Configure environment variables** on both platforms
4. **Test the full workflow** end-to-end
5. **Monitor logs** for any issues
6. **Set up custom domains** (optional)

---

**Your Nova Autonomous Business Agent Platform is ready for production deployment!** 🚀