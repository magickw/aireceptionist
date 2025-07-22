const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const expressWs = require('express-ws');
require('dotenv').config();

const app = express();
expressWs(app); // Initialize express-ws
const port = process.env.PORT || 3001;

// Import routes
const businessRoutes = require('./routes/businesses');
const appointmentRoutes = require('./routes/appointments');
const callLogRoutes = require('./routes/call_logs');
const twilioRoutes = require('./routes/twilio');
const analyticsRoutes = require('./routes/analytics');
const openRouterTestRoutes = require('./routes/openrouter-test');

app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.get('/', (req, res) => {
  res.send('AI Receptionist backend is running!');
});

// Use routes
app.use('/api/businesses', businessRoutes);
app.use('/api/appointments', appointmentRoutes);
app.use('/api/call-logs', callLogRoutes);
app.use('/twilio', twilioRoutes);
app.use('/api/analytics', analyticsRoutes);
app.use('/api/test', openRouterTestRoutes);

app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});