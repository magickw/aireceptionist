const express = require('express');
const router = express.Router();
const db = require('../database');

// Get comprehensive analytics for a business
router.get('/business/:businessId', async (req, res) => {
  try {
    const { businessId } = req.params;
    const { timeframe = '30d' } = req.query;

    // For now, return mock analytics data since the tables may not exist yet
    // In production, this would query actual call_sessions, appointments, etc.
    
    // Generate some realistic mock data
    const mockData = {
      totalCalls: Math.floor(Math.random() * 500) + 100,
      avgCallDuration: Math.floor(Math.random() * 180) + 120, // 2-5 minutes
      appointmentsBooked: Math.floor(Math.random() * 50) + 20,
      successRate: Math.floor(Math.random() * 20) + 80, // 80-100%
      dailyTrends: generateMockDailyTrends(timeframe),
      intentAnalysis: [
        { intent: 'appointment_booking', count: 45, avg_confidence: 0.92 },
        { intent: 'general_inquiry', count: 32, avg_confidence: 0.87 },
        { intent: 'support_request', count: 28, avg_confidence: 0.89 },
        { intent: 'service_info', count: 21, avg_confidence: 0.85 },
        { intent: 'pricing_inquiry', count: 18, avg_confidence: 0.91 }
      ],
      peakHours: generateMockPeakHours(),
      timeframe
    };

    res.json(mockData);
  } catch (err) {
    console.error('Analytics error:', err);
    res.status(500).json({ error: err.message });
  }
});

// Get revenue analytics
router.get('/business/:businessId/revenue', async (req, res) => {
  try {
    const { businessId } = req.params;
    const { timeframe = '30d' } = req.query;

    // Mock revenue data
    const avgAppointmentValue = 150;
    const appointmentRevenue = generateMockRevenueTrends(timeframe);
    const totalRevenue = appointmentRevenue.reduce((sum, day) => sum + day.revenue, 0);

    res.json({
      totalRevenue,
      avgAppointmentValue,
      appointmentRevenue,
      timeframe
    });
  } catch (err) {
    console.error('Revenue analytics error:', err);
    res.status(500).json({ error: err.message });
  }
});

// Get real-time dashboard data
router.get('/business/:businessId/realtime', async (req, res) => {
  try {
    const { businessId } = req.params;

    // Mock real-time data
    const mockRealtime = {
      activeCalls: Math.floor(Math.random() * 5),
      todayStats: {
        calls_today: Math.floor(Math.random() * 25) + 5,
        avg_duration_today: Math.floor(Math.random() * 60) + 120,
        completed_calls: Math.floor(Math.random() * 20) + 5
      },
      recentCalls: generateMockRecentCalls()
    };

    res.json(mockRealtime);
  } catch (err) {
    console.error('Real-time analytics error:', err);
    res.status(500).json({ error: err.message });
  }
});

// Helper functions to generate mock data
function generateMockDailyTrends(timeframe) {
  const days = timeframe === '7d' ? 7 : timeframe === '30d' ? 30 : 90;
  const trends = [];
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    trends.push({
      date: date.toISOString().split('T')[0],
      calls: Math.floor(Math.random() * 20) + 5,
      avg_duration: Math.floor(Math.random() * 60) + 120,
      avg_confidence: (Math.random() * 0.3 + 0.7).toFixed(2)
    });
  }
  
  return trends;
}

function generateMockPeakHours() {
  const hours = [];
  for (let hour = 0; hour < 24; hour++) {
    let calls = 0;
    if (hour >= 8 && hour <= 18) {
      calls = Math.floor(Math.random() * 15) + 5; // Business hours
    } else if (hour >= 19 && hour <= 21) {
      calls = Math.floor(Math.random() * 8) + 2; // Evening
    } else {
      calls = Math.floor(Math.random() * 3); // Night/early morning
    }
    hours.push({ hour, calls });
  }
  return hours;
}

function generateMockRevenueTrends(timeframe) {
  const days = timeframe === '7d' ? 7 : timeframe === '30d' ? 30 : 90;
  const trends = [];
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const appointments = Math.floor(Math.random() * 5) + 1;
    trends.push({
      date: date.toISOString().split('T')[0],
      total_appointments: appointments,
      revenue: appointments * 150
    });
  }
  
  return trends;
}

function generateMockRecentCalls() {
  const calls = [];
  const phoneNumbers = ['+1234567890', '+1987654321', '+1555123456', '+1444555666', '+1777888999'];
  const statuses = ['ended', 'active', 'ended', 'ended', 'ended'];
  
  for (let i = 0; i < 5; i++) {
    const startTime = new Date();
    startTime.setMinutes(startTime.getMinutes() - (i * 30 + Math.random() * 60));
    
    calls.push({
      id: `call_${i + 1}`,
      customer_phone: phoneNumbers[i],
      status: statuses[i],
      started_at: startTime.toISOString(),
      duration_seconds: Math.floor(Math.random() * 300) + 60,
      ai_confidence: (Math.random() * 0.3 + 0.7).toFixed(2)
    });
  }
  
  return calls;
}

module.exports = router;
