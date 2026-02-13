const express = require('express');
const router = express.Router();
const db = require('../database');

// Get AI performance metrics
router.get('/business/:businessId/performance', async (req, res) => {
  try {
    const { businessId } = req.params;
    const { timeframe = '30d' } = req.query;

    // AI confidence trends over time
    const confidenceTrendsQuery = `
      SELECT 
        DATE(cs.started_at) as date,
        AVG(cs.ai_confidence) as avg_confidence,
        COUNT(*) as total_calls,
        COUNT(CASE WHEN cs.ai_confidence >= 0.8 THEN 1 END) as high_confidence_calls,
        COUNT(CASE WHEN cs.status = 'transferred' THEN 1 END) as transferred_calls
      FROM call_sessions cs
      WHERE cs.business_id = $1 
      AND cs.started_at >= NOW() - INTERVAL '${timeframe.replace('d', ' days')}'
      GROUP BY DATE(cs.started_at)
      ORDER BY date DESC
      LIMIT 30
    `;
    
    const confidenceTrends = await db.query(confidenceTrendsQuery, [businessId]);

    // Intent recognition accuracy
    const intentAccuracyQuery = `
      SELECT 
        cm.intent,
        COUNT(*) as total_messages,
        AVG(cm.confidence) as avg_confidence,
        COUNT(CASE WHEN cm.confidence >= 0.8 THEN 1 END) as high_confidence_messages
      FROM conversation_messages cm
      JOIN call_sessions cs ON cm.call_session_id = cs.id
      WHERE cs.business_id = $1 
      AND cm.intent IS NOT NULL
      AND cs.started_at >= NOW() - INTERVAL '${timeframe.replace('d', ' days')}'
      GROUP BY cm.intent
      ORDER BY total_messages DESC
    `;
    
    const intentAccuracy = await db.query(intentAccuracyQuery, [businessId]);

    // Training scenario performance
    const scenarioPerformanceQuery = `
      SELECT 
        COUNT(*) as total_scenarios,
        COUNT(CASE WHEN is_active = true THEN 1 END) as active_scenarios,
        COUNT(CASE WHEN last_tested IS NOT NULL THEN 1 END) as tested_scenarios,
        AVG(success_rate) as avg_success_rate
      FROM ai_training_scenarios
      WHERE business_id = $1
    `;
    
    const scenarioPerformance = await db.query(scenarioPerformanceQuery, [businessId]);

    // Common failure patterns
    const failurePatternsQuery = `
      SELECT 
        cm.intent,
        COUNT(*) as failure_count,
        AVG(cm.confidence) as avg_confidence
      FROM conversation_messages cm
      JOIN call_sessions cs ON cm.call_session_id = cs.id
      WHERE cs.business_id = $1 
      AND cm.confidence < 0.6
      AND cs.started_at >= NOW() - INTERVAL '${timeframe.replace('d', ' days')}'
      GROUP BY cm.intent
      ORDER BY failure_count DESC
      LIMIT 10
    `;
    
    const failurePatterns = await db.query(failurePatternsQuery, [businessId]);

    // Overall metrics
    const overallMetrics = {
      avgConfidence: parseFloat(confidenceTrends.rows.reduce((sum, row) => sum + parseFloat(row.avg_confidence || 0), 0) / Math.max(confidenceTrends.rows.length, 1)).toFixed(3),
      transferRate: confidenceTrends.rows.length > 0 
        ? parseFloat((confidenceTrends.rows.reduce((sum, row) => sum + parseInt(row.transferred_calls), 0) / 
            confidenceTrends.rows.reduce((sum, row) => sum + parseInt(row.total_calls), 0) * 100).toFixed(2))
        : 0,
      highConfidenceRate: confidenceTrends.rows.length > 0
        ? parseFloat((confidenceTrends.rows.reduce((sum, row) => sum + parseInt(row.high_confidence_calls), 0) / 
            confidenceTrends.rows.reduce((sum, row) => sum + parseInt(row.total_calls), 0) * 100).toFixed(2))
        : 0
    };

    res.json({
      confidenceTrends: confidenceTrends.rows,
      intentAccuracy: intentAccuracy.rows,
      scenarioPerformance: scenarioPerformance.rows[0],
      failurePatterns: failurePatterns.rows,
      overallMetrics,
      timeframe
    });
  } catch (err) {
    console.error('AI performance metrics error:', err);
    res.status(500).json({ error: err.message });
  }
});

// Get improvement recommendations
router.get('/business/:businessId/recommendations', async (req, res) => {
  try {
    const { businessId } = req.params;
    const recommendations = [];

    // Check for low confidence scenarios
    const lowConfidenceQuery = `
      SELECT cm.intent, AVG(cm.confidence) as avg_confidence, COUNT(*) as count
      FROM conversation_messages cm
      JOIN call_sessions cs ON cm.call_session_id = cs.id
      WHERE cs.business_id = $1 AND cm.confidence < 0.7 AND cm.intent IS NOT NULL
      GROUP BY cm.intent
      HAVING COUNT(*) >= 3
      ORDER BY avg_confidence ASC
    `;
    
    const lowConfidence = await db.query(lowConfidenceQuery, [businessId]);
    
    lowConfidence.rows.forEach(row => {
      recommendations.push({
        type: 'low_confidence',
        priority: 'high',
        title: `Improve ${row.intent} Intent Recognition`,
        description: `The "${row.intent}" intent has low confidence (${Math.round(row.avg_confidence * 100)}%) across ${row.count} messages. Consider adding more training scenarios.`,
        action: 'create_training_scenario',
        data: { intent: row.intent, confidence: row.avg_confidence }
      });
    });

    // Check for missing training scenarios
    const frequentIntentsQuery = `
      SELECT cm.intent, COUNT(*) as count
      FROM conversation_messages cm
      JOIN call_sessions cs ON cm.call_session_id = cs.id
      WHERE cs.business_id = $1 AND cm.intent IS NOT NULL
      AND cm.intent NOT IN (
        SELECT DISTINCT category FROM ai_training_scenarios WHERE business_id = $1
      )
      GROUP BY cm.intent
      HAVING COUNT(*) >= 5
      ORDER BY count DESC
    `;
    
    const frequentIntents = await db.query(frequentIntentsQuery, [businessId]);
    
    frequentIntents.rows.forEach(row => {
      recommendations.push({
        type: 'missing_scenario',
        priority: 'medium',
        title: `Add Training for ${row.intent}`,
        description: `The "${row.intent}" intent appears frequently (${row.count} times) but has no training scenarios. Consider creating specific training scenarios.`,
        action: 'create_training_scenario',
        data: { intent: row.intent, frequency: row.count }
      });
    });

    // Check for inactive scenarios with high usage
    const inactiveHighUsageQuery = `
      SELECT ats.title, ats.category, COUNT(cm.id) as usage_count
      FROM ai_training_scenarios ats
      LEFT JOIN conversation_messages cm ON ats.category = cm.intent
      JOIN call_sessions cs ON cm.call_session_id = cs.id
      WHERE ats.business_id = $1 AND ats.is_active = false 
      AND cs.business_id = $1
      GROUP BY ats.id, ats.title, ats.category
      HAVING COUNT(cm.id) > 10
    `;
    
    const inactiveHighUsage = await db.query(inactiveHighUsageQuery, [businessId]);
    
    inactiveHighUsage.rows.forEach(row => {
      recommendations.push({
        type: 'inactive_scenario',
        priority: 'medium',
        title: `Reactivate "${row.title}" Scenario`,
        description: `The scenario "${row.title}" is inactive but the ${row.category} intent is being used frequently (${row.usage_count} times). Consider reactivating it.`,
        action: 'activate_scenario',
        data: { scenario: row.title, category: row.category }
      });
    });

    // Check for high transfer rate
    const transferRateQuery = `
      SELECT 
        COUNT(*) as total_calls,
        COUNT(CASE WHEN status = 'transferred' THEN 1 END) as transferred_calls
      FROM call_sessions
      WHERE business_id = $1 AND started_at >= NOW() - INTERVAL '7 days'
    `;
    
    const transferRate = await db.query(transferRateQuery, [businessId]);
    const rate = transferRate.rows[0];
    const transferPercentage = rate.total_calls > 0 ? (rate.transferred_calls / rate.total_calls * 100) : 0;
    
    if (transferPercentage > 30) {
      recommendations.push({
        type: 'high_transfer_rate',
        priority: 'high',
        title: 'High Transfer Rate Detected',
        description: `${Math.round(transferPercentage)}% of calls are being transferred to humans. This indicates the AI needs more training.`,
        action: 'improve_training',
        data: { transferRate: transferPercentage }
      });
    }

    res.json({
      recommendations,
      totalRecommendations: recommendations.length,
      highPriority: recommendations.filter(r => r.priority === 'high').length,
      mediumPriority: recommendations.filter(r => r.priority === 'medium').length
    });
  } catch (err) {
    console.error('AI recommendations error:', err);
    res.status(500).json({ error: err.message });
  }
});

// Log AI improvement action
router.post('/business/:businessId/improvements', async (req, res) => {
  try {
    const { businessId } = req.params;
    const { action_type, description, metadata } = req.body;

    const query = `
      INSERT INTO system_logs (level, message, service, business_id, metadata)
      VALUES ('info', $1, 'ai-improvement', $2, $3)
      RETURNING *
    `;
    
    const result = await db.query(query, [
      `AI Improvement: ${description}`,
      businessId,
      JSON.stringify({ action_type, ...metadata })
    ]);

    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error('AI improvement logging error:', err);
    res.status(500).json({ error: err.message });
  }
});

// Get improvement history
router.get('/business/:businessId/improvements/history', async (req, res) => {
  try {
    const { businessId } = req.params;
    const { limit = 50 } = req.query;

    const query = `
      SELECT created_at, message, metadata
      FROM system_logs
      WHERE business_id = $1 AND service = 'ai-improvement'
      ORDER BY created_at DESC
      LIMIT $2
    `;
    
    const result = await db.query(query, [businessId, limit]);

    res.json({
      improvements: result.rows,
      total: result.rows.length
    });
  } catch (err) {
    console.error('AI improvement history error:', err);
    res.status(500).json({ error: err.message });
  }
});

// Update scenario success rate after testing
router.post('/business/:businessId/scenarios/:scenarioId/update-success-rate', async (req, res) => {
  try {
    const { businessId, scenarioId } = req.params;
    const { success_rate } = req.body;

    const query = `
      UPDATE ai_training_scenarios 
      SET success_rate = $1, updated_at = CURRENT_TIMESTAMP
      WHERE id = $2 AND business_id = $3
      RETURNING *
    `;
    
    const result = await db.query(query, [success_rate, scenarioId, businessId]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Scenario not found' });
    }

    // Log the improvement
    await db.query(
      `INSERT INTO system_logs (level, message, service, business_id, metadata)
       VALUES ('info', 'Scenario success rate updated', 'ai-improvement', $1, $2)`,
      [businessId, JSON.stringify({ scenarioId, success_rate, action: 'update_success_rate' })]
    );

    res.json(result.rows[0]);
  } catch (err) {
    console.error('Update success rate error:', err);
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;