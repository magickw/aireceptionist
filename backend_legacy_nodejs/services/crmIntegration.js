const integrationService = require('./integrationService');
const db = require('../database');
const logger = require('../utils/logger');

async function sendLeadToCRM(leadData, businessId) {
  try {
    // Get active CRM integrations for the business
    const crmIntegrationsQuery = `
      SELECT integration_type, name, credentials, configuration 
      FROM integrations 
      WHERE business_id = $1 AND integration_type IN ('salesforce', 'hubspot', 'pipedrive') 
      AND status = 'connected'
    `;
    
    const result = await db.query(crmIntegrationsQuery, [businessId]);
    
    if (result.rows.length === 0) {
      logger.info('No active CRM integrations found', { businessId });
      return { success: true, message: 'No CRM integrations configured - lead data stored locally' };
    }

    const results = [];
    
    for (const integration of result.rows) {
      try {
        // Decrypt credentials
        const credentials = JSON.parse(integration.credentials);
        
        // Create contact in CRM
        const contactResult = await integrationService.createContact(
          integration.integration_type,
          credentials,
          {
            firstName: leadData.firstName,
            lastName: leadData.lastName,
            phone: leadData.phone,
            email: leadData.email,
            notes: leadData.notes || `Lead from AI Receptionist call on ${new Date().toLocaleDateString()}`
          }
        );

        results.push({
          integration: integration.name,
          success: contactResult.success,
          id: contactResult.id
        });

        logger.info('Lead sent to CRM', {
          businessId,
          integration: integration.name,
          contactId: contactResult.id
        });
        
      } catch (error) {
        logger.error('Failed to send lead to CRM', {
          businessId,
          integration: integration.name,
          error: error.message
        });
        
        results.push({
          integration: integration.name,
          success: false,
          error: error.message
        });
      }
    }

    return { 
      success: true, 
      message: 'Lead processing completed',
      results 
    };
    
  } catch (error) {
    logger.error('Error in sendLeadToCRM', { error: error.message, businessId });
    return { 
      success: false, 
      message: 'Failed to process lead', 
      error: error.message 
    };
  }
}

async function syncAppointmentToCRM(appointmentData, businessId) {
  try {
    // Get active calendar integrations for the business
    const calendarIntegrationsQuery = `
      SELECT integration_type, name, credentials, configuration 
      FROM integrations 
      WHERE business_id = $1 AND integration_type IN ('google_calendar', 'microsoft_outlook', 'calendly') 
      AND status = 'connected'
    `;
    
    const result = await db.query(calendarIntegrationsQuery, [businessId]);
    
    if (result.rows.length === 0) {
      logger.info('No active calendar integrations found', { businessId });
      return { success: true, message: 'No calendar integrations configured - appointment stored locally' };
    }

    const results = [];
    
    for (const integration of result.rows) {
      try {
        // Decrypt credentials
        const credentials = JSON.parse(integration.credentials);
        
        // Create appointment in calendar system
        const appointmentResult = await integrationService.createAppointment(
          integration.integration_type,
          credentials,
          {
            title: appointmentData.title || `Appointment - ${appointmentData.customerName}`,
            description: appointmentData.description || appointmentData.notes,
            startTime: appointmentData.startTime,
            endTime: appointmentData.endTime,
            timeZone: appointmentData.timeZone,
            attendees: appointmentData.customerEmail ? [appointmentData.customerEmail] : []
          }
        );

        results.push({
          integration: integration.name,
          success: appointmentResult.success,
          id: appointmentResult.id,
          link: appointmentResult.link
        });

        logger.info('Appointment synced to calendar', {
          businessId,
          integration: integration.name,
          appointmentId: appointmentResult.id
        });
        
      } catch (error) {
        logger.error('Failed to sync appointment to calendar', {
          businessId,
          integration: integration.name,
          error: error.message
        });
        
        results.push({
          integration: integration.name,
          success: false,
          error: error.message
        });
      }
    }

    return { 
      success: true, 
      message: 'Appointment sync completed',
      results 
    };
    
  } catch (error) {
    logger.error('Error in syncAppointmentToCRM', { error: error.message, businessId });
    return { 
      success: false, 
      message: 'Failed to sync appointment', 
      error: error.message 
    };
  }
}

async function sendNotificationToSlack(message, businessId) {
  try {
    // Get active Slack integrations for the business
    const slackIntegrationsQuery = `
      SELECT integration_type, name, credentials, configuration 
      FROM integrations 
      WHERE business_id = $1 AND integration_type = 'slack' 
      AND status = 'connected'
    `;
    
    const result = await db.query(slackIntegrationsQuery, [businessId]);
    
    if (result.rows.length === 0) {
      logger.info('No active Slack integrations found', { businessId });
      return { success: true, message: 'No Slack integrations configured' };
    }

    const results = [];
    
    for (const integration of result.rows) {
      try {
        // Decrypt credentials
        const credentials = JSON.parse(integration.credentials);
        const config = JSON.parse(integration.configuration || '{}');
        
        // Send notification to Slack
        const notificationResult = await integrationService.integrations.get('slack').sendNotification(
          credentials,
          message,
          config.channel
        );

        results.push({
          integration: integration.name,
          success: notificationResult.success,
          ts: notificationResult.ts
        });

        logger.info('Notification sent to Slack', {
          businessId,
          integration: integration.name
        });
        
      } catch (error) {
        logger.error('Failed to send Slack notification', {
          businessId,
          integration: integration.name,
          error: error.message
        });
        
        results.push({
          integration: integration.name,
          success: false,
          error: error.message
        });
      }
    }

    return { 
      success: true, 
      message: 'Slack notification completed',
      results 
    };
    
  } catch (error) {
    logger.error('Error in sendNotificationToSlack', { error: error.message, businessId });
    return { 
      success: false, 
      message: 'Failed to send Slack notification', 
      error: error.message 
    };
  }
}

async function getActiveIntegrations(businessId) {
  try {
    const query = `
      SELECT integration_type, name, status, last_sync, configuration
      FROM integrations 
      WHERE business_id = $1 
      ORDER BY integration_type, name
    `;
    
    const result = await db.query(query, [businessId]);
    return result.rows;
  } catch (error) {
    logger.error('Error fetching active integrations', { error: error.message, businessId });
    return [];
  }
}

async function syncAllIntegrations(businessId) {
  try {
    const integrations = await getActiveIntegrations(businessId);
    const connectedIntegrations = integrations.filter(i => i.status === 'connected');
    
    if (connectedIntegrations.length === 0) {
      return { success: true, message: 'No active integrations to sync' };
    }

    const results = [];
    
    for (const integration of connectedIntegrations) {
      try {
        // Get credentials for sync
        const credentialsQuery = `
          SELECT credentials 
          FROM integrations 
          WHERE business_id = $1 AND integration_type = $2 AND name = $3
        `;
        
        const credResult = await db.query(credentialsQuery, [businessId, integration.integration_type, integration.name]);
        
        if (credResult.rows.length > 0) {
          const credentials = JSON.parse(credResult.rows[0].credentials);
          const configuration = JSON.parse(integration.configuration || '{}');
          
          const syncResult = await integrationService.syncData(
            integration.integration_type,
            credentials,
            configuration,
            businessId,
            'incremental'
          );

          results.push({
            integration: integration.name,
            success: syncResult.success,
            summary: syncResult.summary
          });

          // Update last sync time
          await db.query(
            'UPDATE integrations SET last_sync = CURRENT_TIMESTAMP WHERE business_id = $1 AND integration_type = $2 AND name = $3',
            [businessId, integration.integration_type, integration.name]
          );
        }
      } catch (error) {
        logger.error('Failed to sync integration', {
          businessId,
          integration: integration.name,
          error: error.message
        });
        
        results.push({
          integration: integration.name,
          success: false,
          error: error.message
        });
      }
    }

    return {
      success: true,
      message: 'Integration sync completed',
      results
    };
    
  } catch (error) {
    logger.error('Error in syncAllIntegrations', { error: error.message, businessId });
    return {
      success: false,
      message: 'Failed to sync integrations',
      error: error.message
    };
  }
}

module.exports = {
  sendLeadToCRM,
  syncAppointmentToCRM,
  sendNotificationToSlack,
  getActiveIntegrations,
  syncAllIntegrations,
};
