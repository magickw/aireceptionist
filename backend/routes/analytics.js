const express = require('express');
const router = express.Router();
const db = require('../database');

// Get comprehensive analytics for a business
router.get('/business/:businessId', async (req, res) => {
  try {
    const { businessId } = req.params;
    const { timeframe = '30d' } = req.query;

    // Calculate date range
    let dateCondition = '';
    let dateParams = [businessId];
    
    if (timeframe === '7d') {
      dateCondition = 'AND started_at >= NOW() - INTERVAL \'7 days\'';
    } else if (timeframe === '30d') {
      dateCondition = 'AND started_at >= NOW() - INTERVAL \'30 days\'';
    } else if (timeframe === '90d') {
      dateCondition = 'AND started_at >= NOW() - INTERVAL \'90 days\'';
    }

    // Total calls from call_sessions
    const totalCallsQuery = `SELECT COUNT(*) FROM call_sessions WHERE business_id = $1 ${dateCondition}`;
    const totalCalls = await db.query(totalCallsQuery, dateParams);

    // Average call duration
    const avgDurationQuery = `SELECT AVG(duration_seconds) FROM call_sessions WHERE business_id = $1 AND duration_seconds IS NOT NULL ${dateCondition}`;
    const avgDuration = await db.query(avgDurationQuery, dateParams);

    // Appointments booked
    const appointmentsQuery = `SELECT COUNT(*) FROM appointments WHERE business_id = $1 AND status = 'confirmed' AND created_at >= NOW() - INTERVAL '${timeframe.replace('d', ' days')}'`;
    const appointmentsBooked = await db.query(appointmentsQuery, [businessId]);

    // Call success rate (calls that didn't end in transfer or error)
    const successfulCallsQuery = `SELECT COUNT(*) FROM call_sessions WHERE business_id = $1 AND status = 'ended' AND ai_confidence >= 0.7 ${dateCondition}`;
    const successfulCalls = await db.query(successfulCallsQuery, dateParams);

    // Daily call trends
    const dailyTrendsQuery = `
      SELECT 
        DATE(started_at) as date,
        COUNT(*) as calls,
        AVG(duration_seconds) as avg_duration,
        AVG(ai_confidence) as avg_confidence
      FROM call_sessions 
      WHERE business_id = $1 ${dateCondition}
      GROUP BY DATE(started_at)
      ORDER BY date DESC
      LIMIT 30
    `;
    const dailyTrends = await db.query(dailyTrendsQuery, dateParams);

    // Call intent analysis
    const intentAnalysisQuery = `
      SELECT 
        cm.intent,
        COUNT(*) as count,
        AVG(cm.confidence) as avg_confidence
      FROM conversation_messages cm
      JOIN call_sessions cs ON cm.call_session_id = cs.id
      WHERE cs.business_id = $1 AND cm.intent IS NOT NULL ${dateCondition.replace('started_at', 'cs.started_at')}
      GROUP BY cm.intent
      ORDER BY count DESC
    `;
    const intentAnalysis = await db.query(intentAnalysisQuery, dateParams);

    // Peak hours analysis
    const peakHoursQuery = `
      SELECT 
        EXTRACT(HOUR FROM started_at) as hour,
        COUNT(*) as calls
      FROM call_sessions
      WHERE business_id = $1 ${dateCondition}
      GROUP BY hour
      ORDER BY hour
    `;
    const peakHours = await db.query(peakHoursQuery, dateParams);

    const totalCallsCount = parseInt(totalCalls.rows[0].count);
    const successfulCallsCount = parseInt(successfulCalls.rows[0].count);
    const successRate = totalCallsCount > 0 ? (successfulCallsCount / totalCallsCount * 100) : 0;

    res.json({
      totalCalls: totalCallsCount,
      avgCallDuration: Math.round(parseFloat(avgDuration.rows[0].avg) || 0),
      appointmentsBooked: parseInt(appointmentsBooked.rows[0].count),
      successRate: Math.round(successRate * 100) / 100,
      dailyTrends: dailyTrends.rows,
      intentAnalysis: intentAnalysis.rows,
      peakHours: peakHours.rows,
      timeframe
    });
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

    // This is a placeholder - in a real app you'd have revenue/billing data
    // For now, we'll estimate based on appointments and call volume
    const appointmentsQuery = `
      SELECT 
        COUNT(*) as total_appointments,
        DATE(created_at) as date
      FROM appointments 
      WHERE business_id = $1 AND status = 'confirmed' 
      AND created_at >= NOW() - INTERVAL '${timeframe.replace('d', ' days')}'
      GROUP BY DATE(created_at)
      ORDER BY date DESC
    `;
    const appointments = await db.query(appointmentsQuery, [businessId]);

    // Estimated revenue (placeholder calculation)
    const avgAppointmentValue = 150; // This would come from business settings
    const totalRevenue = appointments.rows.reduce((sum, row) => sum + (parseInt(row.total_appointments) * avgAppointmentValue), 0);

    res.json({
      totalRevenue,
      avgAppointmentValue,
      appointmentRevenue: appointments.rows,
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

    // Active calls
    const activeCallsQuery = 'SELECT COUNT(*) FROM call_sessions WHERE business_id = $1 AND status = \'active\'';
    const activeCalls = await db.query(activeCallsQuery, [businessId]);

    // Today's stats
    const todayStatsQuery = `
      SELECT 
        COUNT(*) as calls_today,
        AVG(duration_seconds) as avg_duration_today,
        COUNT(CASE WHEN status = 'ended' THEN 1 END) as completed_calls
      FROM call_sessions 
      WHERE business_id = $1 AND DATE(started_at) = CURRENT_DATE
    `;
    const todayStats = await db.query(todayStatsQuery, [businessId]);

    // Recent calls
    const recentCallsQuery = `
      SELECT id, customer_phone, status, started_at, duration_seconds, ai_confidence
      FROM call_sessions 
      WHERE business_id = $1 
      ORDER BY started_at DESC 
      LIMIT 10
    `;
    const recentCalls = await db.query(recentCallsQuery, [businessId]);

    res.json({
      activeCalls: parseInt(activeCalls.rows[0].count),
      todayStats: todayStats.rows[0],
      recentCalls: recentCalls.rows
    });
  } catch (err) {
    console.error('Real-time analytics error:', err);
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
