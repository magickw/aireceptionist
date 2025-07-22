const axios = require('axios');
const { google } = require('googleapis');
const logger = require('../utils/logger');

class IntegrationService {
  constructor() {
    this.integrations = new Map();
    this.initializeIntegrations();
  }

  initializeIntegrations() {
    // Initialize integration handlers
    this.integrations.set('salesforce', new SalesforceIntegration());
    this.integrations.set('hubspot', new HubSpotIntegration());
    this.integrations.set('google_calendar', new GoogleCalendarIntegration());
    this.integrations.set('microsoft_outlook', new MicrosoftOutlookIntegration());
    this.integrations.set('slack', new SlackIntegration());
    this.integrations.set('stripe', new StripeIntegration());
    this.integrations.set('square', new SquareIntegration());
    this.integrations.set('pipedrive', new PipedriveIntegration());
  }

  async syncData(integrationType, credentials, configuration, businessId, syncType = 'full') {
    const integration = this.integrations.get(integrationType);
    if (!integration) {
      throw new Error(`Integration ${integrationType} not found`);
    }

    try {
      const result = await integration.sync(credentials, configuration, businessId, syncType);
      logger.info(`Integration sync completed`, {
        integrationType,
        businessId,
        syncType,
        result: result.summary
      });
      return result;
    } catch (error) {
      logger.error(`Integration sync failed`, {
        integrationType,
        businessId,
        error: error.message
      });
      throw error;
    }
  }

  async testConnection(integrationType, credentials, configuration) {
    const integration = this.integrations.get(integrationType);
    if (!integration) {
      throw new Error(`Integration ${integrationType} not found`);
    }

    return await integration.testConnection(credentials, configuration);
  }

  async createContact(integrationType, credentials, contactData) {
    const integration = this.integrations.get(integrationType);
    if (!integration && integration.createContact) {
      throw new Error(`Contact creation not supported for ${integrationType}`);
    }

    return await integration.createContact(credentials, contactData);
  }

  async createAppointment(integrationType, credentials, appointmentData) {
    const integration = this.integrations.get(integrationType);
    if (!integration && integration.createAppointment) {
      throw new Error(`Appointment creation not supported for ${integrationType}`);
    }

    return await integration.createAppointment(credentials, appointmentData);
  }
}

// Base Integration Class
class BaseIntegration {
  constructor() {
    this.name = 'Base Integration';
    this.type = 'base';
  }

  async testConnection(credentials, configuration) {
    throw new Error('testConnection method must be implemented');
  }

  async sync(credentials, configuration, businessId, syncType) {
    throw new Error('sync method must be implemented');
  }

  async refreshToken(credentials) {
    // Override in OAuth integrations
    return credentials;
  }
}

// Salesforce CRM Integration
class SalesforceIntegration extends BaseIntegration {
  constructor() {
    super();
    this.name = 'Salesforce CRM';
    this.type = 'crm';
    this.baseUrl = 'https://login.salesforce.com';
  }

  async testConnection(credentials, configuration) {
    try {
      const response = await axios.get(`${credentials.instance_url}/services/data/v54.0/sobjects/`, {
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      return {
        success: true,
        data: {
          objects: response.data.sobjects.length,
          org_id: response.headers['sforce-orgid']
        }
      };
    } catch (error) {
      return {
        success: false,
        error: `Salesforce connection failed: ${error.response?.data?.message || error.message}`
      };
    }
  }

  async createContact(credentials, contactData) {
    try {
      const salesforceData = {
        FirstName: contactData.firstName,
        LastName: contactData.lastName,
        Phone: contactData.phone,
        Email: contactData.email,
        LeadSource: 'AI Receptionist Call',
        Description: contactData.notes || 'Created via AI Receptionist'
      };

      const response = await axios.post(
        `${credentials.instance_url}/services/data/v54.0/sobjects/Contact/`,
        salesforceData,
        {
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      return { success: true, id: response.data.id };
    } catch (error) {
      throw new Error(`Failed to create Salesforce contact: ${error.message}`);
    }
  }

  async sync(credentials, configuration, businessId, syncType) {
    // Implement sync logic for Salesforce
    return {
      success: true,
      summary: {
        contacts_synced: 0,
        opportunities_synced: 0,
        activities_synced: 0
      }
    };
  }
}

// HubSpot CRM Integration
class HubSpotIntegration extends BaseIntegration {
  constructor() {
    super();
    this.name = 'HubSpot CRM';
    this.type = 'crm';
    this.baseUrl = 'https://api.hubapi.com';
  }

  async testConnection(credentials, configuration) {
    try {
      const response = await axios.get(`${this.baseUrl}/crm/v3/objects/contacts?limit=1`, {
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      return {
        success: true,
        data: {
          total_contacts: response.data.total,
          account_id: response.data.paging?.next?.after || 'connected'
        }
      };
    } catch (error) {
      return {
        success: false,
        error: `HubSpot connection failed: ${error.response?.data?.message || error.message}`
      };
    }
  }

  async createContact(credentials, contactData) {
    try {
      const hubspotData = {
        properties: {
          firstname: contactData.firstName,
          lastname: contactData.lastName,
          phone: contactData.phone,
          email: contactData.email,
          hs_lead_status: 'NEW',
          lifecyclestage: 'lead'
        }
      };

      const response = await axios.post(
        `${this.baseUrl}/crm/v3/objects/contacts`,
        hubspotData,
        {
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      return { success: true, id: response.data.id };
    } catch (error) {
      throw new Error(`Failed to create HubSpot contact: ${error.message}`);
    }
  }

  async sync(credentials, configuration, businessId, syncType) {
    return {
      success: true,
      summary: {
        contacts_synced: 0,
        deals_synced: 0,
        companies_synced: 0
      }
    };
  }
}

// Google Calendar Integration
class GoogleCalendarIntegration extends BaseIntegration {
  constructor() {
    super();
    this.name = 'Google Calendar';
    this.type = 'calendar';
  }

  async testConnection(credentials, configuration) {
    try {
      const auth = new google.auth.OAuth2();
      auth.setCredentials({
        access_token: credentials.access_token,
        refresh_token: credentials.refresh_token
      });

      const calendar = google.calendar({ version: 'v3', auth });
      const response = await calendar.calendarList.list();

      return {
        success: true,
        data: {
          calendars: response.data.items.length,
          primary_calendar: response.data.items.find(cal => cal.primary)?.summary
        }
      };
    } catch (error) {
      return {
        success: false,
        error: `Google Calendar connection failed: ${error.message}`
      };
    }
  }

  async createAppointment(credentials, appointmentData) {
    try {
      const auth = new google.auth.OAuth2();
      auth.setCredentials({
        access_token: credentials.access_token,
        refresh_token: credentials.refresh_token
      });

      const calendar = google.calendar({ version: 'v3', auth });
      
      const event = {
        summary: appointmentData.title,
        description: appointmentData.description,
        start: {
          dateTime: appointmentData.startTime,
          timeZone: appointmentData.timeZone || 'UTC'
        },
        end: {
          dateTime: appointmentData.endTime,
          timeZone: appointmentData.timeZone || 'UTC'
        },
        attendees: appointmentData.attendees?.map(email => ({ email })) || []
      };

      const response = await calendar.events.insert({
        calendarId: credentials.calendar_id || 'primary',
        resource: event
      });

      return { success: true, id: response.data.id, link: response.data.htmlLink };
    } catch (error) {
      throw new Error(`Failed to create Google Calendar event: ${error.message}`);
    }
  }

  async sync(credentials, configuration, businessId, syncType) {
    return {
      success: true,
      summary: {
        events_synced: 0,
        calendars_synced: 0
      }
    };
  }
}

// Microsoft Outlook Integration
class MicrosoftOutlookIntegration extends BaseIntegration {
  constructor() {
    super();
    this.name = 'Microsoft Outlook';
    this.type = 'calendar';
    this.baseUrl = 'https://graph.microsoft.com/v1.0';
  }

  async testConnection(credentials, configuration) {
    try {
      const response = await axios.get(`${this.baseUrl}/me/calendars`, {
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      return {
        success: true,
        data: {
          calendars: response.data.value.length,
          primary_calendar: response.data.value.find(cal => cal.isDefaultCalendar)?.name
        }
      };
    } catch (error) {
      return {
        success: false,
        error: `Outlook connection failed: ${error.response?.data?.error?.message || error.message}`
      };
    }
  }

  async createAppointment(credentials, appointmentData) {
    try {
      const event = {
        subject: appointmentData.title,
        body: {
          contentType: 'Text',
          content: appointmentData.description || ''
        },
        start: {
          dateTime: appointmentData.startTime,
          timeZone: appointmentData.timeZone || 'UTC'
        },
        end: {
          dateTime: appointmentData.endTime,
          timeZone: appointmentData.timeZone || 'UTC'
        },
        attendees: appointmentData.attendees?.map(email => ({
          emailAddress: {
            address: email,
            name: email
          }
        })) || []
      };

      const response = await axios.post(
        `${this.baseUrl}/me/events`,
        event,
        {
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      return { success: true, id: response.data.id, link: response.data.webLink };
    } catch (error) {
      throw new Error(`Failed to create Outlook event: ${error.message}`);
    }
  }

  async sync(credentials, configuration, businessId, syncType) {
    return {
      success: true,
      summary: {
        events_synced: 0,
        calendars_synced: 0
      }
    };
  }
}

// Slack Integration
class SlackIntegration extends BaseIntegration {
  constructor() {
    super();
    this.name = 'Slack';
    this.type = 'communication';
    this.baseUrl = 'https://slack.com/api';
  }

  async testConnection(credentials, configuration) {
    try {
      const response = await axios.get(`${this.baseUrl}/auth.test`, {
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.ok) {
        return {
          success: true,
          data: {
            team: response.data.team,
            user: response.data.user,
            team_id: response.data.team_id
          }
        };
      } else {
        return {
          success: false,
          error: `Slack connection failed: ${response.data.error}`
        };
      }
    } catch (error) {
      return {
        success: false,
        error: `Slack connection failed: ${error.message}`
      };
    }
  }

  async sendNotification(credentials, message, channel) {
    try {
      const response = await axios.post(`${this.baseUrl}/chat.postMessage`, {
        channel: channel || credentials.default_channel || '#general',
        text: message,
        username: 'AI Receptionist'
      }, {
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      return { success: response.data.ok, ts: response.data.ts };
    } catch (error) {
      throw new Error(`Failed to send Slack message: ${error.message}`);
    }
  }

  async sync(credentials, configuration, businessId, syncType) {
    return {
      success: true,
      summary: {
        channels_synced: 0,
        members_synced: 0
      }
    };
  }
}

// Stripe Integration
class StripeIntegration extends BaseIntegration {
  constructor() {
    super();
    this.name = 'Stripe';
    this.type = 'payment';
    this.baseUrl = 'https://api.stripe.com/v1';
  }

  async testConnection(credentials, configuration) {
    try {
      const response = await axios.get(`${this.baseUrl}/account`, {
        headers: {
          'Authorization': `Bearer ${credentials.secret_key}`,
          'Content-Type': 'application/json'
        }
      });

      return {
        success: true,
        data: {
          account_id: response.data.id,
          business_name: response.data.business_profile?.name,
          country: response.data.country
        }
      };
    } catch (error) {
      return {
        success: false,
        error: `Stripe connection failed: ${error.response?.data?.error?.message || error.message}`
      };
    }
  }

  async createPaymentIntent(credentials, amount, currency = 'usd', metadata = {}) {
    try {
      const response = await axios.post(`${this.baseUrl}/payment_intents`, {
        amount: Math.round(amount * 100), // Convert to cents
        currency,
        metadata
      }, {
        headers: {
          'Authorization': `Bearer ${credentials.secret_key}`,
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      return { success: true, payment_intent: response.data };
    } catch (error) {
      throw new Error(`Failed to create Stripe payment intent: ${error.message}`);
    }
  }

  async sync(credentials, configuration, businessId, syncType) {
    return {
      success: true,
      summary: {
        customers_synced: 0,
        payments_synced: 0,
        subscriptions_synced: 0
      }
    };
  }
}

// Square Integration
class SquareIntegration extends BaseIntegration {
  constructor() {
    super();
    this.name = 'Square';
    this.type = 'payment';
    this.baseUrl = 'https://connect.squareup.com/v2';
  }

  async testConnection(credentials, configuration) {
    try {
      const response = await axios.get(`${this.baseUrl}/locations`, {
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      return {
        success: true,
        data: {
          locations: response.data.locations.length,
          business_name: response.data.locations[0]?.business_name
        }
      };
    } catch (error) {
      return {
        success: false,
        error: `Square connection failed: ${error.response?.data?.errors?.[0]?.detail || error.message}`
      };
    }
  }

  async sync(credentials, configuration, businessId, syncType) {
    return {
      success: true,
      summary: {
        locations_synced: 0,
        customers_synced: 0,
        orders_synced: 0
      }
    };
  }
}

// Pipedrive Integration
class PipedriveIntegration extends BaseIntegration {
  constructor() {
    super();
    this.name = 'Pipedrive';
    this.type = 'crm';
  }

  async testConnection(credentials, configuration) {
    try {
      const response = await axios.get(`https://${credentials.company_domain}.pipedrive.com/api/v1/users/me?api_token=${credentials.api_token}`);

      return {
        success: true,
        data: {
          user_id: response.data.data.id,
          company: response.data.data.company_name,
          email: response.data.data.email
        }
      };
    } catch (error) {
      return {
        success: false,
        error: `Pipedrive connection failed: ${error.response?.data?.error || error.message}`
      };
    }
  }

  async createContact(credentials, contactData) {
    try {
      const pipedriveData = {
        name: `${contactData.firstName} ${contactData.lastName}`,
        phone: contactData.phone,
        email: contactData.email,
        add_time: new Date().toISOString()
      };

      const response = await axios.post(
        `https://${credentials.company_domain}.pipedrive.com/api/v1/persons?api_token=${credentials.api_token}`,
        pipedriveData
      );

      return { success: true, id: response.data.data.id };
    } catch (error) {
      throw new Error(`Failed to create Pipedrive contact: ${error.message}`);
    }
  }

  async sync(credentials, configuration, businessId, syncType) {
    return {
      success: true,
      summary: {
        persons_synced: 0,
        deals_synced: 0,
        activities_synced: 0
      }
    };
  }
}

module.exports = new IntegrationService();