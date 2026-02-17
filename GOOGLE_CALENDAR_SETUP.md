# Google Calendar Integration Setup Guide

This guide will help you set up Google Calendar OAuth2 for the AI Receptionist.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **Select a project** → **New Project**
3. Enter project name (e.g., "AI Receptionist")
4. Click **Create**

## Step 2: Enable Google Calendar API

1. In your project, go to **APIs & Services** → **Library**
2. Search for "Google Calendar API"
3. Click on it, then click **Enable**

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (for production use) or **Internal** (for testing only)
3. Click **Create**
4. Fill in:
   - **App name**: AI Receptionist
   - **User support email**: Your email
   - **Developer contact**: Your email
5. Click **Save and Continue** (skip other sections for now)
6. Click **Back to Dashboard**

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Select **Web application**
4. Fill in:
   - **Name**: AI Receptionist Web
   - **Authorized redirect URIs**:
     - `https://receptium.onrender.com/api/calendar/google/callback`
     - `http://localhost:3000/api/calendar/google/callback` (for local testing)
5. Click **Create**

## Step 5: Get Your Credentials

After creating, you'll see a popup with:
- **Client ID**: Copy this
- **Client Secret**: Copy this

## Step 6: Add Environment Variables

Add these to your **Render** backend environment variables:

```
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=https://receptium.onrender.com/api/calendar/google/callback
```

## Step 7: Update Redirect URI in Code (if needed)

The redirect URI in your code should match exactly what you configured in Google Cloud Console.

Current redirect URI in code: `https://your-domain.com/api/calendar/google/callback`

You may need to update this to match your actual domain.

## Step 8: Test the Integration

1. Redeploy your backend on Render with the new environment variables
2. Navigate to the calendar integration page in your app
3. Click "Connect Google Calendar"
4. You should be redirected to Google's OAuth consent screen
5. Authorize the app
6. The integration should be connected

## Troubleshooting

**Error: "invalid_client"**
- Double-check your Client ID and Client Secret
- Make sure there are no extra spaces

**Error: "redirect_uri_mismatch"**
- Ensure the redirect URI in Google Console matches exactly
- Check for trailing slashes or protocol differences (http vs https)

**Error: "access_denied"**
- Check OAuth consent screen configuration
- Make sure your Google account is listed as a test user (if using Internal consent screen)

## Additional Notes

- The Google Calendar integration supports:
  - Creating events
  - Checking availability
  - Getting available slots
  - Syncing appointments

- Tokens are automatically refreshed when they expire
- The integration checks for conflicts in both your database and Google Calendar