# Quick Start: Deploy to Vercel

This guide will help you deploy the entire AI Receptionist project to Vercel in minutes.

## 🚀 One-Click Deployment

### Option 1: Deploy with Vercel CLI (Recommended)

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Login to Vercel
vercel login

# 3. Deploy from project root
cd /Users/bfguo/Apps/aireceptionist
vercel
```

### Option 2: Deploy via Vercel Dashboard

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Vercel will auto-detect the configuration
4. Add environment variables (see below)
5. Click **Deploy**

## 📝 Required Environment Variables

Add these in Vercel Dashboard → Settings → Environment Variables:

### Database (Required)
```
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

Get one from:
- [Supabase](https://supabase.com) - Free tier available
- [Neon](https://neon.tech) - Free tier available
- [Railway](https://railway.app) - Free tier available

### AWS (Required for AI features)
```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
```

### Application (Required)
```
API_V1_STR=/api/v1
PROJECT_NAME=AI Receptionist
SECRET_KEY=generate_with_openssl_rand_hex_32
```

Generate SECRET_KEY:
```bash
openssl rand -hex 32
```

### Optional Services
```
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_number
REDIS_URL=redis://your_redis_url
```

## 🗄️ Database Setup

### Quick Start with Supabase (Free)

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Go to Settings → Database
4. Copy the "Connection string" (make sure to include your password)
5. Use it as `DATABASE_URL`

### Run Migrations

Option 1: Using seed script
```bash
export DATABASE_URL="postgresql://user:pass@host:port/dbname"
python backend/seed_business_templates.py
```

Option 2: Manual SQL
Copy the SQL from `backend/alembic/versions/*.py` files and run in your database tool.

## ✅ Verify Deployment

After deployment, check:

1. **Frontend**: `https://your-project.vercel.app` ✅
2. **Backend API**: `https://your-project.vercel.app/api/v1/health` ✅
3. **Landing Page**: `https://your-project.vercel.app/landing` ✅

## 🎯 What Gets Deployed

### Frontend (Next.js)
- Landing page with all features
- Dashboard with analytics
- All admin tools
- Mobile-responsive design

### Backend (FastAPI - Serverless)
- AI Receptionist API
- Voice/Chat functionality
- Appointment & Order management
- Admin template management
- All integrations

## 💡 Tips

### Free Tier Limits
- Vercel Free: 100GB bandwidth/month, 6000 function minutes
- Supabase Free: 500MB database, 2GB bandwidth/month
- AWS Bedrock: Pay-per-use (check pricing)

### Optimization
- Enable caching where possible
- Use database connection pooling
- Optimize database queries
- Minimize cold starts

### Monitoring
- Check Vercel Dashboard for logs
- Monitor database usage
- Track AWS costs

## 🆘 Troubleshooting

### Database Connection Error
- Verify `DATABASE_URL` format
- Check if database allows Vercel IPs
- Enable connection pooling

### 504 Timeout
- Serverless functions have 10-60s timeout
- Optimize long-running operations
- Consider using Vercel Edge Functions

### Build Failures
- Check Vercel build logs
- Verify all dependencies are in requirements.txt
- Ensure Python version is set to 3.10

## 📚 Full Documentation

See [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md) for detailed deployment guide.

## 🎉 You're Ready!

Your AI Receptionist is now running on Vercel with:
- ✅ No server management
- ✅ Auto-scaling
- ✅ Free SSL
- ✅ Global CDN
- ✅ Git integration

Enjoy your cloud-hosted AI Receptionist!