# Calendly Integration - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Set Up Calendly OAuth App (2 minutes)

1. Go to [Calendly Developer Portal](https://developer.calendly.com/)
2. Click **"Create New App"**
3. Fill in:
   - **App Name**: AI Receptionist Pro
   - **Redirect URI**: `http://localhost:8000/api/v1/calendly/callback/calendly` (for local dev)
   - **Permissions**: `calendar_events:read`, `calendar_events:write`
4. Copy your **Client ID** and **Client Secret**

### Step 2: Configure Environment (1 minute)

Add to `backend/.env`:

```bash
# For local development
CALENDLY_CLIENT_ID=your_client_id_here
CALENDLY_CLIENT_SECRET=your_client_secret_here
CALENDLY_REDIRECT_URI=http://localhost:8000/api/v1/calendly/callback/calendly
CALENDLY_WEBHOOK_SECRET=test_secret_for_now
```

### Step 3: Restart Backend (30 seconds)

```bash
cd backend
source venv/bin/activate  # or .venv\Scripts\Activate on Windows
python -m uvicorn app.main:app --reload --port 8000
```

### Step 4: Connect Calendly (1 minute)

1. Open browser: `http://localhost:3000/calendly`
2. Click **"Connect Calendly"**
3. Authorize the app in Calendly
4. You'll be redirected back with success message

### Step 5: Test It Out! (30 seconds)

Try these API endpoints:

```bash
# Check connection status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/calendar

# Get event types
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/calendly/1/event-types

# Get upcoming events
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/calendly/1/events
```

## 🎯 What You Can Do Now

### View Event Types
See all your Calendly booking event types in the dashboard

### See Upcoming Bookings
View next 30 days of scheduled appointments

### Real-Time Updates
Set up webhooks to get instant notifications when:
- Someone books an appointment
- A booking is canceled
- A booking is rescheduled

## 🔧 Optional: Set Up Webhooks

For real-time sync, configure webhooks:

### Local Development (using ngrok)

```bash
# Install ngrok if you don't have it
brew install ngrok  # macOS
# or download from https://ngrok.com

# Start ngrok
ngrok http 8000
```

Copy the HTTPS URL and:

1. In Calendly developer portal, add webhook subscription:
   - **URL**: `https://YOUR_NGROK_URL/api/v1/calendly/webhooks/handler`
   - **Events**: `invitee.created`, `invitee.canceled`, `invitee_rescheduled`

2. Update `.env`:
   ```bash
   CALENDLY_WEBHOOK_SECRET=your_webhook_secret_from_calendly
   ```

## 🐛 Troubleshooting

### "Failed to exchange code"
- ✅ Check Client ID/Secret are correct (no extra spaces)
- ✅ Verify redirect URI matches exactly
- ✅ Ensure Calendly account has API access

### "Integration not found"
- ✅ Make sure you completed OAuth flow
- ✅ Check database has calendar_integrations record
- ✅ Verify business_id is correct

### CORS errors in frontend
- ✅ Add your frontend URL to CORS_ORIGINS in backend `.env`
- ✅ Example: `CORS_ORIGINS=http://localhost:3000,https://your-domain.com`

## 📚 Next Steps

1. **Explore the Dashboard** - Navigate to `/calendly` to see your integration
2. **Read Full Docs** - Check out `CALENDLY_INTEGRATION.md` for complete details
3. **Test Webhooks** - Create a test booking in Calendly and watch it appear
4. **Integrate with AI** - Use automation workflows with Calendly data

## 💡 Pro Tips

- **Token Auto-Refresh**: Tokens refresh automatically, but you'll see warnings 30 mins before expiry
- **Event Filtering**: Use date range filters to get specific events
- **Multi-Business**: Each business can connect their own Calendly account
- **Webhook Security**: Always verify signatures in production

## 🆘 Need Help?

- **API Docs**: See `CALENDLY_INTEGRATION.md` for full endpoint reference
- **Logs**: Check `logs/api.log` for detailed error messages
- **Calendly Docs**: https://developer.calendly.com/api-docs
- **Support**: support@aireceptionist.com

---

**That's it! You're ready to use Calendly integration! 🎉**

Happy scheduling! 📅
