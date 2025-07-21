const db = require('../database');
const { google } = require('googleapis');

// Configure Google Calendar API (replace with your actual credentials and setup)
const calendar = google.calendar({
  version: 'v3',
  auth: new google.auth.GoogleAuth({
    scopes: ['https://www.googleapis.com/auth/calendar'],
    keyFile: process.env.GOOGLE_APPLICATION_CREDENTIALS, // Path to your service account key file
  }),
});

async function bookAppointment(businessId, customerName, customerPhone, appointmentTime, serviceType) {
  try {
    // Save to our internal database
    const { rows } = await db.query(
      'INSERT INTO appointments (business_id, customer_name, customer_phone, appointment_time, service_type) VALUES ($1, $2, $3, $4, $5) RETURNING *',
      [businessId, customerName, customerPhone, appointmentTime, serviceType]
    );
    const newAppointment = rows[0];

    // Integrate with Google Calendar
    const event = {
      summary: `${serviceType} for ${customerName}`,
      description: `Phone: ${customerPhone}`,
      start: {
        dateTime: appointmentTime,
        timeZone: 'America/Los_Angeles', // Adjust timezone as needed
      },
      end: {
        dateTime: new Date(new Date(appointmentTime).getTime() + 60 * 60 * 1000).toISOString(), // Assuming 1 hour duration
        timeZone: 'America/Los_Angeles', // Adjust timezone as needed
      },
      attendees: [
        { email: 'your-business-email@example.com' }, // Replace with your business email
        { email: 'customer-email@example.com' }, // If you collect customer email
      ],
      reminders: {
        useDefault: false,
        overrides: [
          { method: 'email', minutes: 24 * 60 },
          { method: 'popup', minutes: 10 },
        ],
      },
    };

    // Replace 'primary' with the actual calendar ID if you have a specific one
    const calendarId = 'primary'; 

    const googleCalendarResponse = await calendar.events.insert({
      calendarId: calendarId,
      resource: event,
    });

    console.log('Google Calendar event created:', googleCalendarResponse.data.htmlLink);

    return { success: true, appointment: newAppointment, googleCalendarEvent: googleCalendarResponse.data };
  } catch (error) {
    console.error('Error booking appointment:', error);
    return { success: false, error: error.message };
  }
}

// Add more action processing functions here (e.g., takeMessage, sendNotification)

module.exports = {
  bookAppointment,
};