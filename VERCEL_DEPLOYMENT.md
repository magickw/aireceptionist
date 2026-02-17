# Vercel Deployment Guide

This guide will help you deploy the entire AI Receptionist project (frontend + backend) on Vercel.

## Prerequisites

1. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
2. **PostgreSQL Database** - You'll need a hosted PostgreSQL database (we recommend Supabase, Neon, or Railway)
3. **AWS Account** - For AWS Bedrock (Nova AI), AWS Transcribe, and AWS Polly
4. **Twilio Account** - For voice functionality (optional)
5. **Redis** - For caching (optional, can use Upstash)

## Architecture Overview

```
Vercel Deployment:
├── Frontend (Next.js) → /path → Serves the React frontend
└── Backend (FastAPI) → /api/* → Serverless functions
```

## Step 1: Database Setup

### Option A: Supabase (Recommended)
1. Go to [supabase.com](https://supabase.com) and create a new project
2. Get your connection string from Settings → Database
3. Copy the connection URL (format: `postgresql://user:pass@host:port/dbname`)

### Option B: Neon
1. Go to [neon.tech](https://neon.tech) and create a new project
2. Copy the connection string from the dashboard

### Option C: Railway
1. Go to [railway.app](https://railway.app) and create a PostgreSQL database
2. Copy the connection string

## Step 2: Environment Variables

Set these environment variables in Vercel (Settings → Environment Variables):

### Database
```
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### AWS (Required for AI features)
```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
```

### Backend Configuration
```
API_V1_STR=/api/v1
PROJECT_NAME=AI Receptionist
SECRET_KEY=your_secret_key_here_generate_with_openssl_rand_hex_32
```

### Optional Services
```
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_number
REDIS_URL=redis://your_redis_url
```

## Step 3: Deploy to Vercel

### Option A: Via Vercel CLI (Recommended)

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy from root directory:
```bash
cd /Users/bfguo/Apps/aireceptionist
vercel
```

4. Follow the prompts:
   - Set up and deploy? → **Yes**
   - Which scope? → Select your account
   - Link to existing project? → **No**
   - What's your project's name? → `aireceptionist`
   - In which directory is your code located? → `./`
   - Want to override the settings? → **No**

5. Vercel will detect the configuration and deploy both frontend and backend

### Option B: Via Vercel Dashboard

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Next.js (for frontend)
   - **Root Directory**: `./`
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `.next` (auto-detected)

4. Add environment variables in Settings → Environment Variables

5. Click **Deploy**

## Step 4: Run Database Migrations

After deployment, you need to run migrations on your PostgreSQL database:

```bash
# Connect to your database using psql or your database tool
# Then run the migration files in order:

# 1. Initial schema
# See backend/alembic/versions/001_initial_schema.py

# 2. Add operating hours
# See backend/alembic/versions/002_add_operating_hours_to_businesses.py

# 3. Add new models
# See backend/alembic/versions/20260214_1113_4eb65017697a_add_new_models_and_call_session_fields.py

# 4. Add menu items
# See backend/alembic/versions/20260214_1759_06e159e4634e_add_menu_items_table.py

# 5. Add business license
# See backend/alembic/versions/20260214_1813_5f3ff61738d1_add_business_license_to_businesses.py

# 6. Add unit to menu items
# See backend/alembic/versions/20260215_1411_4550b31fe1b0_add_unit_to_menu_items.py

# 7. Add approval requests
# See backend/alembic/versions/20260215_1533_dbb0f09407e8_add_approval_requests_and_manager_.py

# 8. Add business templates (NEW)
# See backend/alembic/versions/20260217_1200_add_business_templates_and_models.py
```

Or use the seed script:
```bash
# Set DATABASE_URL
export DATABASE_URL="postgresql://user:pass@host:port/dbname"

# Run seed script
python backend/seed_business_templates.py
```

## Step 5: Verify Deployment

1. **Frontend**: Access `https://your-project.vercel.app`
2. **Backend API**: Test at `https://your-project.vercel.app/api/v1/health`
3. **Landing Page**: Access `https://your-project.vercel.app/landing`

## Step 6: Configure Domain (Optional)

1. Go to Vercel Dashboard → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed

## Troubleshooting

### Issue: Database connection errors
- Verify `DATABASE_URL` is correct
- Check if your database allows connections from Vercel's IP ranges
- For Supabase: Enable "Connection Pooling" mode

### Issue: AWS Bedrock errors
- Verify AWS credentials are correct
- Check if AWS Bedrock is available in your region
- Ensure your IAM user has necessary permissions

### Issue: Functions timing out
- Vercel serverless functions have a 10-60 second timeout
- Long-running operations (like model training) may need optimization
- Consider using Vercel Cron Jobs for scheduled tasks

### Issue: WebSocket connections failing
- WebSocket support is limited in serverless functions
- Consider using Vercel Edge Functions for real-time features
- Or use a dedicated WebSocket service (like Pusher)

## Cost Optimization

### Vercel Free Tier Includes:
- 100GB bandwidth per month
- 6,000 minutes of serverless function execution
- Unlimited projects
- SSL certificates
- Automatic deployments

### Backend Optimization:
- Enable response caching where possible
- Use database connection pooling
- Optimize database queries
- Minimize cold starts with warm functions

## Monitoring

1. **Vercel Dashboard**: View logs, analytics, and performance
2. **Database Monitoring**: Use your database provider's dashboard
3. **AWS CloudWatch**: Monitor AWS service usage

## Scaling

As your application grows:

1. **Upgrade Vercel Plan**: For more execution time and bandwidth
2. **Database Scaling**: Upgrade your PostgreSQL plan
3. **CDN**: Vercel's edge network automatically handles static assets
4. **Load Balancing**: Vercel automatically handles load balancing

## Rollback

If you need to rollback:

```bash
vercel rollback
```

Or use the Vercel Dashboard to deploy a previous commit.

## Support

- Vercel Documentation: https://vercel.com/docs
- FastAPI on Vercel: https://vercel.com/guides/fastapi
- Database Help: Consult your database provider's documentation