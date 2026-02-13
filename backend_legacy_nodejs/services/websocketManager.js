const WebSocket = require('ws');
const logger = require('../utils/logger');
const { AppError } = require('../middleware/errorHandler');
const db = require('../database');

class WebSocketManager {
  constructor() {
    this.clients = new Map();
    this.callSessions = new Map();
    this.dashboardClients = new Map(); // Clients subscribed to dashboard updates
  }

  initialize(server) {
    this.wss = new WebSocket.Server({ 
      server,
      path: '/ws'
    });

    this.wss.on('connection', this.handleConnection.bind(this));
    
    // Start real-time analytics broadcasting
    this.startAnalyticsBroadcast();
    
    logger.info('WebSocket server initialized');
  }

  handleConnection(ws, req) {
    const clientId = this.generateClientId();
    
    logger.info('New WebSocket connection', {
      clientId,
      ip: req.socket.remoteAddress,
      userAgent: req.headers['user-agent']
    });

    // Store client connection
    this.clients.set(clientId, {
      ws,
      id: clientId,
      connectedAt: new Date(),
      lastPing: new Date(),
      businessId: null,
      subscriptions: []
    });

    // Set up client
    ws.clientId = clientId;
    ws.isAlive = true;

    // Handle messages
    ws.on('message', (data) => {
      this.handleMessage(ws, data);
    });

    // Handle connection close
    ws.on('close', (code, reason) => {
      this.handleDisconnection(ws, code, reason);
    });

    // Handle errors
    ws.on('error', (error) => {
      logger.error('WebSocket error', {
        clientId,
        error: error.message
      });
    });

    // Handle pong responses
    ws.on('pong', () => {
      const client = this.clients.get(clientId);
      if (client) {
        client.lastPing = new Date();
        ws.isAlive = true;
      }
    });

    // Send welcome message
    this.sendToClient(clientId, {
      type: 'connection',
      status: 'connected',
      clientId,
      timestamp: new Date().toISOString()
    });
  }

  handleMessage(ws, data) {
    try {
      const message = JSON.parse(data);
      const clientId = ws.clientId;

      logger.debug('WebSocket message received', {
        clientId,
        type: message.type
      });

      switch (message.type) {
        case 'join_call':
          this.handleJoinCall(clientId, message);
          break;
        
        case 'leave_call':
          this.handleLeaveCall(clientId, message);
          break;
        
        case 'audio_data':
          this.handleAudioData(clientId, message);
          break;
        
        case 'call_control':
          this.handleCallControl(clientId, message);
          break;

        case 'subscribe_dashboard':
          this.handleDashboardSubscription(clientId, message);
          break;

        case 'unsubscribe_dashboard':
          this.handleDashboardUnsubscription(clientId, message);
          break;

        case 'request_analytics':
          this.handleAnalyticsRequest(clientId, message);
          break;
        
        case 'ping':
          this.sendToClient(clientId, { type: 'pong', timestamp: new Date().toISOString() });
          break;
        
        default:
          logger.warn('Unknown message type', {
            clientId,
            type: message.type
          });
      }
    } catch (error) {
      logger.error('Error handling WebSocket message', {
        clientId: ws.clientId,
        error: error.message
      });
    }
  }

  handleDisconnection(ws, code, reason) {
    const clientId = ws.clientId;
    
    logger.info('WebSocket disconnection', {
      clientId,
      code,
      reason: reason.toString()
    });

    // Remove from active calls
    this.removeClientFromCalls(clientId);
    
    // Remove from dashboard subscriptions
    this.dashboardClients.delete(clientId);
    
    // Remove from clients
    this.clients.delete(clientId);
  }

  handleDashboardSubscription(clientId, message) {
    const { businessId } = message;
    
    if (!businessId) {
      return this.sendToClient(clientId, {
        type: 'error',
        message: 'Business ID is required for dashboard subscription'
      });
    }

    const client = this.clients.get(clientId);
    if (client) {
      client.businessId = businessId;
      client.subscriptions = message.subscriptions || ['analytics', 'calls', 'appointments'];
      this.dashboardClients.set(clientId, client);

      this.sendToClient(clientId, {
        type: 'dashboard_subscribed',
        businessId,
        subscriptions: client.subscriptions,
        timestamp: new Date().toISOString()
      });

      // Send initial data
      this.sendInitialDashboardData(clientId, businessId);
    }
  }

  handleDashboardUnsubscription(clientId, message) {
    this.dashboardClients.delete(clientId);
    const client = this.clients.get(clientId);
    if (client) {
      client.businessId = null;
      client.subscriptions = [];
    }

    this.sendToClient(clientId, {
      type: 'dashboard_unsubscribed',
      timestamp: new Date().toISOString()
    });
  }

  async handleAnalyticsRequest(clientId, message) {
    const { businessId, type } = message;
    
    if (!businessId) {
      return this.sendToClient(clientId, {
        type: 'error',
        message: 'Business ID is required'
      });
    }

    try {
      let data = null;

      switch (type) {
        case 'realtime':
          data = await this.getRealTimeAnalytics(businessId);
          break;
        case 'daily':
          data = await this.getDailyAnalytics(businessId);
          break;
        case 'performance':
          data = await this.getPerformanceMetrics(businessId);
          break;
        default:
          data = await this.getRealTimeAnalytics(businessId);
      }

      this.sendToClient(clientId, {
        type: 'analytics_data',
        requestType: type,
        data,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Error fetching analytics data', {
        clientId,
        businessId,
        error: error.message
      });

      this.sendToClient(clientId, {
        type: 'error',
        message: 'Failed to fetch analytics data'
      });
    }
  }

  async sendInitialDashboardData(clientId, businessId) {
    try {
      const [realTimeData, dailyData] = await Promise.all([
        this.getRealTimeAnalytics(businessId),
        this.getDailyAnalytics(businessId)
      ]);

      this.sendToClient(clientId, {
        type: 'dashboard_initial_data',
        data: {
          realTime: realTimeData,
          daily: dailyData
        },
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Error sending initial dashboard data', {
        clientId,
        businessId,
        error: error.message
      });
    }
  }

  async getRealTimeAnalytics(businessId) {
    const activeCallsQuery = 'SELECT COUNT(*) FROM call_sessions WHERE business_id = $1 AND status = \'active\'';
    const todayStatsQuery = `
      SELECT 
        COUNT(*) as calls_today,
        AVG(duration_seconds) as avg_duration_today,
        COUNT(CASE WHEN status = 'ended' THEN 1 END) as completed_calls
      FROM call_sessions 
      WHERE business_id = $1 AND DATE(started_at) = CURRENT_DATE
    `;
    const recentCallsQuery = `
      SELECT id, customer_phone, status, started_at, duration_seconds, ai_confidence
      FROM call_sessions 
      WHERE business_id = $1 
      ORDER BY started_at DESC 
      LIMIT 5
    `;

    const [activeCalls, todayStats, recentCalls] = await Promise.all([
      db.query(activeCallsQuery, [businessId]),
      db.query(todayStatsQuery, [businessId]),
      db.query(recentCallsQuery, [businessId])
    ]);

    return {
      activeCalls: parseInt(activeCalls.rows[0].count),
      todayStats: todayStats.rows[0],
      recentCalls: recentCalls.rows
    };
  }

  async getDailyAnalytics(businessId) {
    const dailyTrendsQuery = `
      SELECT 
        DATE(started_at) as date,
        COUNT(*) as calls,
        AVG(duration_seconds) as avg_duration,
        AVG(ai_confidence) as avg_confidence
      FROM call_sessions 
      WHERE business_id = $1 AND started_at >= NOW() - INTERVAL '7 days'
      GROUP BY DATE(started_at)
      ORDER BY date DESC
    `;

    const result = await db.query(dailyTrendsQuery, [businessId]);
    return result.rows;
  }

  async getPerformanceMetrics(businessId) {
    const performanceQuery = `
      SELECT 
        AVG(ai_confidence) as avg_confidence,
        COUNT(CASE WHEN status = 'transferred' THEN 1 END) as transferred_calls,
        COUNT(*) as total_calls
      FROM call_sessions 
      WHERE business_id = $1 AND started_at >= NOW() - INTERVAL '24 hours'
    `;

    const result = await db.query(performanceQuery, [businessId]);
    const data = result.rows[0];
    
    return {
      avgConfidence: parseFloat(data.avg_confidence || 0),
      transferRate: data.total_calls > 0 ? (data.transferred_calls / data.total_calls * 100) : 0,
      totalCalls: parseInt(data.total_calls)
    };
  }

  // Broadcast analytics updates to subscribed dashboard clients
  startAnalyticsBroadcast() {
    this.analyticsInterval = setInterval(async () => {
      const businessClients = new Map();
      
      // Group clients by business ID
      this.dashboardClients.forEach((client) => {
        if (client.businessId && client.subscriptions.includes('analytics')) {
          if (!businessClients.has(client.businessId)) {
            businessClients.set(client.businessId, []);
          }
          businessClients.get(client.businessId).push(client.id);
        }
      });

      // Send updates to each business
      for (const [businessId, clientIds] of businessClients) {
        try {
          const analyticsData = await this.getRealTimeAnalytics(businessId);
          
          clientIds.forEach(clientId => {
            this.sendToClient(clientId, {
              type: 'analytics_update',
              data: analyticsData,
              timestamp: new Date().toISOString()
            });
          });
        } catch (error) {
          logger.error('Error broadcasting analytics update', {
            businessId,
            error: error.message
          });
        }
      }
    }, 10000); // Broadcast every 10 seconds
  }

  // Broadcast call events to dashboard clients
  broadcastCallEvent(businessId, event, data) {
    this.dashboardClients.forEach((client) => {
      if (client.businessId === businessId && client.subscriptions.includes('calls')) {
        this.sendToClient(client.id, {
          type: 'call_event',
          event,
          data,
          timestamp: new Date().toISOString()
        });
      }
    });
  }

  // Broadcast appointment events to dashboard clients
  broadcastAppointmentEvent(businessId, event, data) {
    this.dashboardClients.forEach((client) => {
      if (client.businessId === businessId && client.subscriptions.includes('appointments')) {
        this.sendToClient(client.id, {
          type: 'appointment_event',
          event,
          data,
          timestamp: new Date().toISOString()
        });
      }
    });
  }

  handleJoinCall(clientId, message) {
    const { callId, role } = message;
    
    if (!callId) {
      return this.sendToClient(clientId, {
        type: 'error',
        message: 'Call ID is required'
      });
    }

    // Create or get call session
    if (!this.callSessions.has(callId)) {
      this.callSessions.set(callId, {
        id: callId,
        participants: new Map(),
        createdAt: new Date(),
        status: 'active'
      });
    }

    const callSession = this.callSessions.get(callId);
    
    // Add client to call
    callSession.participants.set(clientId, {
      clientId,
      role: role || 'participant',
      joinedAt: new Date()
    });

    logger.info('Client joined call', {
      callId,
      clientId,
      role,
      participantCount: callSession.participants.size
    });

    // Notify client
    this.sendToClient(clientId, {
      type: 'call_joined',
      callId,
      role,
      participantCount: callSession.participants.size
    });

    // Notify other participants
    this.broadcastToCall(callId, {
      type: 'participant_joined',
      clientId,
      role,
      participantCount: callSession.participants.size
    }, clientId);
  }

  handleLeaveCall(clientId, message) {
    const { callId } = message;
    
    if (this.callSessions.has(callId)) {
      const callSession = this.callSessions.get(callId);
      callSession.participants.delete(clientId);

      logger.info('Client left call', {
        callId,
        clientId,
        participantCount: callSession.participants.size
      });

      // Notify other participants
      this.broadcastToCall(callId, {
        type: 'participant_left',
        clientId,
        participantCount: callSession.participants.size
      });

      // Clean up empty calls
      if (callSession.participants.size === 0) {
        this.callSessions.delete(callId);
        logger.info('Call session ended', { callId });
      }
    }
  }

  handleAudioData(clientId, message) {
    const { callId, audioData, format } = message;
    
    if (!this.callSessions.has(callId)) {
      return this.sendToClient(clientId, {
        type: 'error',
        message: 'Call not found'
      });
    }

    // Process audio data (implement your audio processing here)
    const processedAudio = this.processAudioData(audioData, format);
    
    // Broadcast to other participants in the call
    this.broadcastToCall(callId, {
      type: 'audio_data',
      senderId: clientId,
      audioData: processedAudio,
      format,
      timestamp: new Date().toISOString()
    }, clientId);
  }

  handleCallControl(clientId, message) {
    const { callId, action } = message;
    
    logger.info('Call control action', {
      callId,
      clientId,
      action
    });

    // Broadcast control action to all participants
    this.broadcastToCall(callId, {
      type: 'call_control',
      senderId: clientId,
      action,
      timestamp: new Date().toISOString()
    });
  }

  processAudioData(audioData, format) {
    // Implement audio processing logic here
    // This could include:
    // - Format conversion
    // - Noise reduction
    // - Compression
    // - Encryption
    
    // For now, just return the data as-is
    return audioData;
  }

  sendToClient(clientId, data) {
    const client = this.clients.get(clientId);
    if (client && client.ws.readyState === WebSocket.OPEN) {
      try {
        client.ws.send(JSON.stringify(data));
      } catch (error) {
        logger.error('Error sending to client', {
          clientId,
          error: error.message
        });
      }
    }
  }

  broadcastToCall(callId, data, excludeClientId = null) {
    const callSession = this.callSessions.get(callId);
    if (!callSession) return;

    callSession.participants.forEach((participant) => {
      if (participant.clientId !== excludeClientId) {
        this.sendToClient(participant.clientId, data);
      }
    });
  }

  removeClientFromCalls(clientId) {
    this.callSessions.forEach((callSession, callId) => {
      if (callSession.participants.has(clientId)) {
        callSession.participants.delete(clientId);
        
        // Notify other participants
        this.broadcastToCall(callId, {
          type: 'participant_disconnected',
          clientId,
          participantCount: callSession.participants.size
        });

        // Clean up empty calls
        if (callSession.participants.size === 0) {
          this.callSessions.delete(callId);
          logger.info('Call session ended due to no participants', { callId });
        }
      }
    });
  }

  generateClientId() {
    return 'client_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Health check and cleanup
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      this.wss.clients.forEach((ws) => {
        if (!ws.isAlive) {
          logger.info('Terminating inactive WebSocket connection', {
            clientId: ws.clientId
          });
          return ws.terminate();
        }

        ws.isAlive = false;
        ws.ping();
      });
    }, 30000); // Check every 30 seconds
  }

  // Get statistics
  getStats() {
    return {
      connectedClients: this.clients.size,
      activeCalls: this.callSessions.size,
      dashboardClients: this.dashboardClients.size,
      totalParticipants: Array.from(this.callSessions.values())
        .reduce((total, call) => total + call.participants.size, 0)
    };
  }

  // Graceful shutdown
  shutdown() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    if (this.analyticsInterval) {
      clearInterval(this.analyticsInterval);
    }

    this.clients.forEach((client) => {
      client.ws.close(1000, 'Server shutting down');
    });

    logger.info('WebSocket server shutdown');
  }
}

module.exports = new WebSocketManager();