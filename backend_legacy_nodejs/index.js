const express = require('express');
const http = require('http');
const bodyParser = require('body-parser');
const cors = require('cors');
const cookieParser = require('cookie-parser');
const helmet = require('helmet');
const compression = require('compression');
require('dotenv').config();

// Import middleware and services
const { globalErrorHandler } = require('./middleware/errorHandler');
const { requestId, requestLogger, apiLimiter } = require('./middleware/requestMiddleware');
const websocketManager = require('./services/websocketManager');
const logger = require('./utils/logger');

const app = express();
const server = http.createServer(app);
const port = process.env.PORT || 3001;

// Security middleware
app.use(helmet({
  contentSecurityPolicy: process.env.NODE_ENV === 'production'
}));

// Request processing middleware
app.use(compression());
app.use(requestId);
app.use(requestLogger);

// CORS configuration
const corsOptions = {
  origin: process.env.NODE_ENV === 'production' 
    ? process.env.FRONTEND_URL 
    : ['http://localhost:3000', 'http://localhost:3003'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID']
};

app.use(cors(corsOptions));
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));
app.use(cookieParser());

// Rate limiting
app.use('/api', apiLimiter);

// Health check endpoint
app.get('/health', (req, res) => {
  const wsStats = websocketManager.getStats();
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    websocket: wsStats
  });
});

app.get('/', (req, res) => {
  res.json({
    message: 'AI Receptionist Backend API',
    version: '2.0.0',
    status: 'running',
    endpoints: {
      auth: '/api/auth',
      businesses: '/api/businesses',
      appointments: '/api/appointments',
      callLogs: '/api/call-logs',
      analytics: '/api/analytics',
      aiTraining: '/api/ai-training',
      aiImprovement: '/api/ai-improvement',
      integrations: '/api/integrations',
      twilio: '/twilio',
      websocket: '/ws'
    }
  });
});

// Import routes
const authRoutes = require('./routes/auth');
const businessRoutes = require('./routes/businesses');
const appointmentRoutes = require('./routes/appointments');
const callLogRoutes = require('./routes/call_logs');
const twilioRoutes = require('./routes/twilio');
const analyticsRoutes = require('./routes/analytics');
const aiTrainingRoutes = require('./routes/aiTraining');
const aiImprovementRoutes = require('./routes/aiImprovement');
const integrationsRoutes = require('./routes/integrations');
const openRouterTestRoutes = require('./routes/openrouter-test');

// Use routes
app.use('/api/auth', authRoutes);
app.use('/api/businesses', businessRoutes);
app.use('/api/appointments', appointmentRoutes);
app.use('/api/call-logs', callLogRoutes);
app.use('/twilio', twilioRoutes);
app.use('/api/analytics', analyticsRoutes);
app.use('/api/ai-training', aiTrainingRoutes);
app.use('/api/ai-improvement', aiImprovementRoutes);
app.use('/api/integrations', integrationsRoutes);
app.use('/api/test', openRouterTestRoutes);

// Initialize WebSocket server
websocketManager.initialize(server);
websocketManager.startHeartbeat();

// Global error handling middleware (must be last)
app.use(globalErrorHandler);

// Handle uncaught exceptions
process.on('uncaughtException', (err) => {
  logger.error('Uncaught Exception! Shutting down...', {
    error: err.message,
    stack: err.stack
  });
  process.exit(1);
});

// Handle unhandled promise rejections
process.on('unhandledRejection', (err) => {
  logger.error('Unhandled Rejection! Shutting down...', {
    error: err.message,
    stack: err.stack
  });
  server.close(() => {
    process.exit(1);
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received. Shutting down gracefully...');
  websocketManager.shutdown();
  server.close(() => {
    logger.info('Process terminated');
    process.exit(0);
  });
});

server.listen(port, () => {
  logger.info('Server started successfully', {
    port,
    environment: process.env.NODE_ENV || 'development',
    timestamp: new Date().toISOString()
  });
});