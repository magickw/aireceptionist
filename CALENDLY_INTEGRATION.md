# Calendly Integration Guide

## Overview

The AI Receptionist Pro now includes comprehensive Calendly integration, allowing you to:

- **Sync appointments** automatically from Calendly to your AI receptionist
- **Manage bookings** through the dashboard
- **Receive real-time webhook notifications** for new bookings, cancellations, and reschedules
- **View event types** and upcoming events
- **OAuth 2.0 authentication** for secure connection

## Setup Instructions

### 1. Prerequisites

You need a Calendly account with API access. If you don't have one:
1. Go to [Calendly.com](https://calendly.com) and create an account
2. Upgrade to a plan that supports API access (Professional or higher)

### 2. Create Calendly OAuth App

1. Log in to your Calendly account
2. Go to [Calendly Developer Portal](https://developer.calendly.com/)
3. Click "Create New App"
4. Fill in the app details:
   - **App Name**: AI Receptionist Pro
   - **Redirect URI**: `https://your-domain.com/api/v1/calendly/callback/calendly`
   - **Permissions**: Select `calendar_events:read` and `calendar_events:write`
5. Save your app to get:
   - **Client ID**
   - **Client Secret**

### 3. Configure Backend Environment

Add the following to your `backend/.env` file:

```env
# Calendly OAuth
CALENDLY_CLIENT_ID=your_calendly_client_id
CALENDLY_CLIENT_SECRET=your_calendly_client_secret
CALENDLY_REDIRECT_URI=https://your-domain.com/api/v1/calendly/callback/calendly
CALENDLY_WEBHOOK_SECRET=your_calendly_webhook_secret
```

For local development:
```env
CALENDLY_REDIRECT_URI=http://localhost:8000/api/v1/calendly/callback/calendly
```

### 4. Connect Calendly in the Dashboard

1. Start your backend and frontend servers
2. Navigate to **Integrations → Calendly** or go to `/calendly`
3. Click **"Connect Calendly"**
4. You'll be redirected to Calendly's authorization page
5. Log in and authorize the application
6. You'll be redirected back to the dashboard with Calendly connected

### 5. Configure Webhooks (Optional but Recommended)

To receive real-time notifications when bookings are made or canceled:

1. In your Calendly app dashboard, go to **Webhooks**
2. Add a new webhook subscription:
   - **URL**: `https://your-domain.com/api/v1/calendly/webhooks/handler`
   - **Events to subscribe to**:
     - `invitee.created` (new booking)
     - `invitee.canceled` (cancellation)
     - `invitee_rescheduled` (rescheduled booking)
3. Copy the **Webhook Secret** and add it to your `.env`:
   ```env
   CALENDLY_WEBHOOK_SECRET=your_calendly_webhook_secret
   ```

Alternatively, use the API endpoint to create webhooks programmatically.

## API Endpoints

### OAuth & Connection

- **GET** `/api/v1/calendly/connect/calendly` - Get OAuth authorization URL
- **POST** `/api/v1/calendly/callback/calendly?code={code}&state={state}` - OAuth callback handler

### Event Management

- **GET** `/api/v1/calendly/{integration_id}/event-types` - Get all event types
- **GET** `/api/v1/calendly/{integration_id}/events` - Get scheduled events
  - Query params: `start_time`, `end_time`

### Webhooks

- **POST** `/api/v1/calendly/{integration_id}/webhooks` - Create webhook subscription
- **DELETE** `/api/v1/calendly/{integration_id}/webhooks/{subscription_id}` - Delete webhook
- **POST** `/api/v1/calendly/webhooks/handler` - Handle incoming webhooks

### Status

- **GET** `/api/v1/calendly/{integration_id}/status` - Get integration status and token expiration

## Features

### 1. Automatic Appointment Sync

When a booking is made in Calendly:
- The appointment is automatically created in the AI Receptionist database
- Customer information is synced (name, email, phone)
- Event details (type, time, duration) are preserved
- Status is tracked (confirmed, canceled, rescheduled)

### 2. Real-Time Webhooks

Receive instant notifications for:
- **New Bookings**: `invitee.created`
- **Cancellations**: `invitee.canceled`
- **Reschedules**: `invitee_rescheduled`

Webhooks are verified using HMAC-SHA256 signatures for security.

### 3. Event Type Management

View all available event types from your Calendly account:
- Event name and description
- Duration in minutes
- Active/inactive status

### 4. Upcoming Events Dashboard

View all upcoming events for the next 30 days:
- Event type
- Invitee name and email
- Start and end times
- Booking status

### 5. Token Management

Automatic token refresh when access tokens expire (every 2 hours):
- Tokens are encrypted in the database
- Warning when token is expiring soon
- One-click reconnection if needed

## Database Schema

The integration uses the existing `calendar_integrations` table:

```sql
CREATE TABLE calendar_integrations (
    id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(id),
    provider VARCHAR(50) NOT NULL, -- 'google', 'outlook', 'calendly'
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    calendar_id VARCHAR(255), -- Stores Calendly user URI
    status VARCHAR(20) DEFAULT 'active',
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Troubleshooting

### "Failed to exchange Calendly code"

- Verify your Client ID and Secret are correct
- Ensure the redirect URI matches exactly what's configured in Calendly
- Check that your Calendly account has API access enabled

### "Invalid webhook signature"

- Verify the webhook secret matches in both Calendly and your `.env`
- Ensure the secret is copied without extra spaces or characters

### "Token expired" error

- The system should auto-refresh tokens, but if it fails:
- Disconnect and reconnect Calendly
- Check that the refresh token is stored in the database

### Events not syncing

- Check the integration status is "active"
- Verify the Calendly account has events scheduled
- Check backend logs for any errors during sync

## Security Considerations

1. **Token Encryption**: All OAuth tokens are encrypted using AES-256 before storage
2. **Signature Verification**: Webhooks are verified using HMAC-SHA256
3. **State Parameter**: OAuth flow uses state parameter to prevent CSRF attacks
4. **Scoped Access**: Only requests necessary permissions (calendar read/write)

## Integration with Other Features

### AI Voice Agent

When Calendly is connected, the AI voice agent can:
- Check availability by querying Calendly events
- Inform callers about booked slots
- Redirect to Calendly for self-service booking

### Automation Workflows

Use Nova Act automation to:
- Automatically book appointments via Calendly UI automation
- Sync customer data to CRM after booking
- Send follow-up emails based on Calendly events

### Analytics

Calendly bookings contribute to:
- Appointment volume metrics
- No-show tracking
- Customer engagement scores

## Best Practices

1. **Enable Webhooks**: Always set up webhooks for real-time sync
2. **Monitor Token Expiry**: Keep an eye on token expiration warnings
3. **Test in Sandbox**: Use Calendly's sandbox environment for testing
4. **Rate Limiting**: Respect Calendly's API rate limits (currently 100 requests/minute)
5. **Error Handling**: Implement proper error handling for failed API calls

## Support

For issues or questions:
- Check the [Calendly API Documentation](https://developer.calendly.com/api-docs)
- Review backend logs for detailed error messages
- Contact support at support@aireceptionist.com

## Future Enhancements

Planned features:
- Two-way sync (create Calendly events from AI receptionist)
- Multi-calendar support for multiple team members
- Custom webhook event routing
- Advanced scheduling rules and constraints
- Bulk event import/export
