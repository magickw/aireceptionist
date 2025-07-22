const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const axios = require('axios');
const db = require('../database');
const logger = require('../utils/logger');

// Encryption key for storing sensitive credentials
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || crypto.randomBytes(32);
const ENCRYPTION_ALGORITHM = 'aes-256-gcm';

// Helper function to encrypt data
function encrypt(text) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipher(ENCRYPTION_ALGORITHM, ENCRYPTION_KEY);
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  const authTag = cipher.getAuthTag();
  return {
    encrypted,
    iv: iv.toString('hex'),
    authTag: authTag.toString('hex')
  };
}

// Helper function to decrypt data
function decrypt(encryptedData) {
  const decipher = crypto.createDecipher(ENCRYPTION_ALGORITHM, ENCRYPTION_KEY);
  decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));
  let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
}

// Get all integrations for a business
router.get('/business/:businessId', async (req, res) => {
  try {
    const { businessId } = req.params;
    
    const query = `
      SELECT id, integration_type, name, status, configuration, last_sync, error_message, created_at, updated_at
      FROM integrations 
      WHERE business_id = $1 
      ORDER BY integration_type, name
    `;
    
    const result = await db.query(query, [businessId]);
    
    // Don't return encrypted credentials in the response
    const integrations = result.rows.map(integration => ({
      ...integration,
      credentials: undefined // Remove credentials from response
    }));
    
    res.json(integrations);
  } catch (err) {
    console.error('Error fetching integrations:', err);
    res.status(500).json({ error: err.message });
  }
});

// Get available integration types
router.get('/types', async (req, res) => {
  try {
    const integrationTypes = [
      {
        type: 'crm',
        name: 'CRM Systems',
        description: 'Customer relationship management platforms',
        integrations: [
          {
            id: 'salesforce',
            name: 'Salesforce',
            description: 'World\'s #1 CRM platform for customer data and sales tracking',
            features: ['Contact management', 'Lead tracking', 'Opportunity management', 'Activity logging'],
            authType: 'oauth2',
            icon: 'salesforce',
            status: 'available'
          },
          {
            id: 'hubspot',
            name: 'HubSpot CRM',
            description: 'All-in-one marketing, sales, and service platform',
            features: ['Contact sync', 'Deal tracking', 'Marketing automation', 'Email campaigns'],
            authType: 'oauth2',
            icon: 'hubspot',
            status: 'available'
          },
          {
            id: 'pipedrive',
            name: 'Pipedrive',
            description: 'Sales-focused CRM built for pipelines',
            features: ['Pipeline management', 'Deal tracking', 'Activity scheduling', 'Sales reporting'],
            authType: 'api_key',
            icon: 'pipedrive',
            status: 'available'
          }
        ]
      },
      {
        type: 'calendar',
        name: 'Calendar Systems',
        description: 'Schedule and appointment management',
        integrations: [
          {
            id: 'google_calendar',
            name: 'Google Calendar',
            description: 'Sync appointments with Google Calendar',
            features: ['Appointment sync', 'Availability checking', 'Meeting reminders', 'Multi-calendar support'],
            authType: 'oauth2',
            icon: 'google_calendar',
            status: 'available'
          },
          {
            id: 'microsoft_outlook',
            name: 'Microsoft Outlook',
            description: 'Connect with Outlook calendar and email',
            features: ['Calendar integration', 'Email notifications', 'Contact sync', 'Meeting scheduling'],
            authType: 'oauth2',
            icon: 'microsoft',
            status: 'available'
          },
          {
            id: 'calendly',
            name: 'Calendly',
            description: 'Automated scheduling platform',
            features: ['Booking link integration', 'Availability sync', 'Custom booking rules', 'Team scheduling'],
            authType: 'api_key',
            icon: 'calendly',
            status: 'available'
          }
        ]
      },
      {
        type: 'communication',
        name: 'Communication',
        description: 'Messaging and notification platforms',
        integrations: [
          {
            id: 'slack',
            name: 'Slack',
            description: 'Team communication and notifications',
            features: ['Call notifications', 'Appointment alerts', 'Team updates', 'Channel posting'],
            authType: 'oauth2',
            icon: 'slack',
            status: 'available'
          },
          {
            id: 'microsoft_teams',
            name: 'Microsoft Teams',
            description: 'Enterprise communication platform',
            features: ['Meeting notifications', 'Channel updates', 'File sharing', 'Video calls'],
            authType: 'oauth2',
            icon: 'teams',
            status: 'available'
          },
          {
            id: 'discord',
            name: 'Discord',
            description: 'Community communication platform',
            features: ['Server notifications', 'Channel messages', 'Voice channels', 'Custom bots'],
            authType: 'webhook',
            icon: 'discord',
            status: 'available'
          }
        ]
      },
      {
        type: 'payment',
        name: 'Payment Processing',
        description: 'Payment and billing systems',
        integrations: [
          {
            id: 'stripe',
            name: 'Stripe',
            description: 'Online payment processing platform',
            features: ['Payment collection', 'Invoice generation', 'Subscription billing', 'Customer data'],
            authType: 'api_key',
            icon: 'stripe',
            status: 'available'
          },
          {
            id: 'square',
            name: 'Square',
            description: 'Point of sale and payment processing',
            features: ['POS integration', 'Inventory sync', 'Payment processing', 'Customer profiles'],
            authType: 'oauth2',
            icon: 'square',
            status: 'available'
          },
          {
            id: 'paypal',
            name: 'PayPal',
            description: 'Global payment solution',
            features: ['Payment processing', 'Invoice creation', 'Subscription management', 'Dispute handling'],
            authType: 'oauth2',
            icon: 'paypal',
            status: 'available'
          }
        ]
      },
      {
        type: 'analytics',
        name: 'Analytics & Reporting',
        description: 'Data analysis and reporting tools',
        integrations: [
          {
            id: 'google_analytics',
            name: 'Google Analytics',
            description: 'Web and call analytics platform',
            features: ['Call tracking', 'Conversion analytics', 'Performance reports', 'Custom dashboards'],
            authType: 'oauth2',
            icon: 'google_analytics',
            status: 'available'
          },
          {
            id: 'mixpanel',
            name: 'Mixpanel',
            description: 'Product analytics platform',
            features: ['Event tracking', 'User analytics', 'Funnel analysis', 'A/B testing'],
            authType: 'api_key',
            icon: 'mixpanel',
            status: 'available'
          }
        ]
      },
      {
        type: 'ecommerce',
        name: 'E-commerce',
        description: 'Online store and marketplace platforms',
        integrations: [
          {
            id: 'shopify',
            name: 'Shopify',
            description: 'E-commerce platform for online stores',
            features: ['Product catalog', 'Order management', 'Customer sync', 'Inventory tracking'],
            authType: 'oauth2',
            icon: 'shopify',
            status: 'available'
          },
          {
            id: 'woocommerce',
            name: 'WooCommerce',
            description: 'WordPress e-commerce plugin',
            features: ['Product sync', 'Order tracking', 'Customer data', 'Sales reporting'],
            authType: 'api_key',
            icon: 'woocommerce',
            status: 'available'
          }
        ]
      }
    ];
    
    res.json(integrationTypes);
  } catch (err) {
    console.error('Error fetching integration types:', err);
    res.status(500).json({ error: err.message });
  }
});

// Create or update integration
router.post('/business/:businessId', async (req, res) => {
  try {
    const { businessId } = req.params;
    const { integration_type, integration_id, name, configuration, credentials } = req.body;

    // Encrypt credentials if provided
    let encryptedCredentials = null;
    if (credentials && Object.keys(credentials).length > 0) {
      encryptedCredentials = encrypt(JSON.stringify(credentials));
    }

    const query = `
      INSERT INTO integrations (business_id, integration_type, name, status, configuration, credentials, created_at, updated_at)
      VALUES ($1, $2, $3, 'connecting', $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
      ON CONFLICT (business_id, integration_type, name) 
      DO UPDATE SET 
        configuration = $4,
        credentials = $5,
        status = 'connecting',
        updated_at = CURRENT_TIMESTAMP
      RETURNING id, integration_type, name, status, configuration, created_at, updated_at
    `;

    const result = await db.query(query, [
      businessId,
      integration_id,
      name,
      JSON.stringify(configuration || {}),
      JSON.stringify(encryptedCredentials)
    ]);

    const integration = result.rows[0];

    // Test the integration connection
    try {
      const testResult = await testIntegrationConnection(integration_id, credentials, configuration);
      
      if (testResult.success) {
        await db.query(
          'UPDATE integrations SET status = $1, last_sync = CURRENT_TIMESTAMP WHERE id = $2',
          ['connected', integration.id]
        );
        integration.status = 'connected';
      } else {
        await db.query(
          'UPDATE integrations SET status = $1, error_message = $2 WHERE id = $3',
          ['error', testResult.error, integration.id]
        );
        integration.status = 'error';
        integration.error_message = testResult.error;
      }
    } catch (testError) {
      logger.error('Integration test failed:', testError);
      await db.query(
        'UPDATE integrations SET status = $1, error_message = $2 WHERE id = $3',
        ['error', testError.message, integration.id]
      );
    }

    // Log integration creation
    await db.query(
      `INSERT INTO system_logs (level, message, service, business_id, metadata) 
       VALUES ('info', 'Integration created/updated', 'integration', $1, $2)`,
      [businessId, JSON.stringify({ integration_type: integration_id, name, status: integration.status })]
    );

    res.status(201).json(integration);
  } catch (err) {
    console.error('Error creating integration:', err);
    res.status(500).json({ error: err.message });
  }
});

// Delete integration
router.delete('/business/:businessId/integration/:integrationId', async (req, res) => {
  try {
    const { businessId, integrationId } = req.params;

    const query = 'DELETE FROM integrations WHERE id = $1 AND business_id = $2 RETURNING name, integration_type';
    const result = await db.query(query, [integrationId, businessId]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Integration not found' });
    }

    // Log integration deletion
    await db.query(
      `INSERT INTO system_logs (level, message, service, business_id, metadata) 
       VALUES ('info', 'Integration deleted', 'integration', $1, $2)`,
      [businessId, JSON.stringify(result.rows[0])]
    );
    
    res.json({ message: 'Integration deleted successfully' });
  } catch (err) {
    console.error('Error deleting integration:', err);
    res.status(500).json({ error: err.message });
  }
});

// Test integration connection
router.post('/business/:businessId/test/:integrationId', async (req, res) => {
  try {
    const { businessId, integrationId } = req.params;
    const { credentials, configuration } = req.body;

    const testResult = await testIntegrationConnection(integrationId, credentials, configuration);
    
    if (testResult.success) {
      res.json({ success: true, message: 'Connection successful', data: testResult.data });
    } else {
      res.status(400).json({ success: false, error: testResult.error });
    }
  } catch (err) {
    console.error('Error testing integration:', err);
    res.status(500).json({ error: err.message });
  }
});

// Get OAuth URL for supported integrations
router.post('/oauth/url', async (req, res) => {
  try {
    const { integration_id, business_id, redirect_uri } = req.body;
    
    const oauthUrl = generateOAuthURL(integration_id, business_id, redirect_uri);
    
    if (!oauthUrl) {
      return res.status(400).json({ error: 'OAuth not supported for this integration' });
    }
    
    res.json({ oauth_url: oauthUrl });
  } catch (err) {
    console.error('Error generating OAuth URL:', err);
    res.status(500).json({ error: err.message });
  }
});

// Handle OAuth callback
router.post('/oauth/callback', async (req, res) => {
  try {
    const { integration_id, code, state, business_id } = req.body;
    
    const tokenData = await exchangeOAuthCode(integration_id, code, state);
    
    if (tokenData.success) {
      // Store the tokens securely
      const encryptedCredentials = encrypt(JSON.stringify(tokenData.credentials));
      
      await db.query(
        `INSERT INTO integrations (business_id, integration_type, name, status, credentials, created_at, updated_at)
         VALUES ($1, $2, $3, 'connected', $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
         ON CONFLICT (business_id, integration_type, name) 
         DO UPDATE SET credentials = $4, status = 'connected', updated_at = CURRENT_TIMESTAMP`,
        [business_id, integration_id, getIntegrationName(integration_id), JSON.stringify(encryptedCredentials)]
      );
      
      res.json({ success: true, message: 'Integration connected successfully' });
    } else {
      res.status(400).json({ success: false, error: tokenData.error });
    }
  } catch (err) {
    console.error('Error handling OAuth callback:', err);
    res.status(500).json({ error: err.message });
  }
});

// Sync data for specific integration
router.post('/business/:businessId/sync/:integrationId', async (req, res) => {
  try {
    const { businessId, integrationId } = req.params;
    
    // Get integration details
    const integrationQuery = 'SELECT * FROM integrations WHERE id = $1 AND business_id = $2';
    const integrationResult = await db.query(integrationQuery, [integrationId, businessId]);
    
    if (integrationResult.rows.length === 0) {
      return res.status(404).json({ error: 'Integration not found' });
    }
    
    const integration = integrationResult.rows[0];
    
    // Decrypt credentials
    let credentials = {};
    if (integration.credentials) {
      const encryptedCredentials = JSON.parse(integration.credentials);
      credentials = JSON.parse(decrypt(encryptedCredentials));
    }
    
    // Perform sync based on integration type
    const syncResult = await performIntegrationSync(
      integration.integration_type,
      credentials,
      JSON.parse(integration.configuration || '{}'),
      businessId
    );
    
    if (syncResult.success) {
      // Update last sync time
      await db.query(
        'UPDATE integrations SET last_sync = CURRENT_TIMESTAMP, status = $1 WHERE id = $2',
        ['connected', integrationId]
      );
      
      res.json({ success: true, message: 'Sync completed successfully', data: syncResult.data });
    } else {
      await db.query(
        'UPDATE integrations SET status = $1, error_message = $2 WHERE id = $3',
        ['error', syncResult.error, integrationId]
      );
      
      res.status(400).json({ success: false, error: syncResult.error });
    }
  } catch (err) {
    console.error('Error syncing integration:', err);
    res.status(500).json({ error: err.message });
  }
});

// Helper Functions

async function testIntegrationConnection(integrationId, credentials, configuration) {
  try {
    switch (integrationId) {
      case 'salesforce':
        return await testSalesforceConnection(credentials);
      case 'hubspot':
        return await testHubSpotConnection(credentials);
      case 'google_calendar':
        return await testGoogleCalendarConnection(credentials);
      case 'slack':
        return await testSlackConnection(credentials);
      case 'stripe':
        return await testStripeConnection(credentials);
      default:
        return { success: true, message: 'Test connection not implemented for this integration' };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function testSalesforceConnection(credentials) {
  try {
    const response = await axios.get(`${credentials.instance_url}/services/data/v54.0/sobjects/`, {
      headers: {
        'Authorization': `Bearer ${credentials.access_token}`,
        'Content-Type': 'application/json'
      }
    });
    return { success: true, data: { objects: response.data.sobjects.length } };
  } catch (error) {
    return { success: false, error: 'Failed to connect to Salesforce: ' + error.message };
  }
}

async function testHubSpotConnection(credentials) {
  try {
    const response = await axios.get('https://api.hubapi.com/crm/v3/objects/contacts?limit=1', {
      headers: {
        'Authorization': `Bearer ${credentials.access_token}`,
        'Content-Type': 'application/json'
      }
    });
    return { success: true, data: { contacts: response.data.total } };
  } catch (error) {
    return { success: false, error: 'Failed to connect to HubSpot: ' + error.message };
  }
}

async function testGoogleCalendarConnection(credentials) {
  try {
    const response = await axios.get('https://www.googleapis.com/calendar/v3/users/me/calendarList', {
      headers: {
        'Authorization': `Bearer ${credentials.access_token}`,
        'Content-Type': 'application/json'
      }
    });
    return { success: true, data: { calendars: response.data.items.length } };
  } catch (error) {
    return { success: false, error: 'Failed to connect to Google Calendar: ' + error.message };
  }
}

async function testSlackConnection(credentials) {
  try {
    const response = await axios.get('https://slack.com/api/auth.test', {
      headers: {
        'Authorization': `Bearer ${credentials.access_token}`,
        'Content-Type': 'application/json'
      }
    });
    return { success: response.data.ok, data: { team: response.data.team } };
  } catch (error) {
    return { success: false, error: 'Failed to connect to Slack: ' + error.message };
  }
}

async function testStripeConnection(credentials) {
  try {
    const response = await axios.get('https://api.stripe.com/v1/account', {
      headers: {
        'Authorization': `Bearer ${credentials.secret_key}`,
        'Content-Type': 'application/json'
      }
    });
    return { success: true, data: { account_id: response.data.id } };
  } catch (error) {
    return { success: false, error: 'Failed to connect to Stripe: ' + error.message };
  }
}

function generateOAuthURL(integrationId, businessId, redirectUri) {
  // This is a simplified example - in production you'd use proper OAuth libraries
  const baseUrls = {
    'google_calendar': 'https://accounts.google.com/o/oauth2/v2/auth',
    'salesforce': 'https://login.salesforce.com/services/oauth2/authorize',
    'hubspot': 'https://app.hubspot.com/oauth/authorize',
    'slack': 'https://slack.com/oauth/v2/authorize',
    'microsoft_outlook': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
  };
  
  const baseUrl = baseUrls[integrationId];
  if (!baseUrl) return null;
  
  const params = new URLSearchParams({
    client_id: process.env[`${integrationId.toUpperCase()}_CLIENT_ID`],
    redirect_uri: redirectUri,
    response_type: 'code',
    state: `${businessId}_${Date.now()}`,
    scope: getIntegrationScopes(integrationId)
  });
  
  return `${baseUrl}?${params.toString()}`;
}

function getIntegrationScopes(integrationId) {
  const scopes = {
    'google_calendar': 'https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events',
    'salesforce': 'api refresh_token',
    'hubspot': 'crm.objects.contacts.read crm.objects.contacts.write',
    'slack': 'channels:read chat:write',
    'microsoft_outlook': 'https://graph.microsoft.com/calendars.read https://graph.microsoft.com/calendars.readwrite'
  };
  
  return scopes[integrationId] || '';
}

async function exchangeOAuthCode(integrationId, code, state) {
  // Implementation would vary by provider
  // This is a placeholder for the OAuth token exchange
  return {
    success: true,
    credentials: {
      access_token: 'mock_access_token',
      refresh_token: 'mock_refresh_token',
      expires_in: 3600
    }
  };
}

function getIntegrationName(integrationId) {
  const names = {
    'salesforce': 'Salesforce CRM',
    'hubspot': 'HubSpot CRM',
    'google_calendar': 'Google Calendar',
    'slack': 'Slack',
    'stripe': 'Stripe',
    'microsoft_outlook': 'Microsoft Outlook'
  };
  
  return names[integrationId] || integrationId;
}

async function performIntegrationSync(integrationType, credentials, configuration, businessId) {
  // Placeholder for actual sync implementation
  // This would contain the logic for syncing data with each integration
  return {
    success: true,
    data: {
      synced_items: 0,
      last_sync: new Date().toISOString()
    }
  };
}

module.exports = router;