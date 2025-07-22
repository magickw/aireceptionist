const express = require('express');
const router = express.Router();
const db = require('../database');

// Get all training scenarios for a business
router.get('/business/:businessId/scenarios', async (req, res) => {
  try {
    const { businessId } = req.params;
    
    const query = `
      SELECT id, title, description, category, user_input, expected_response, 
             is_active, success_rate, last_tested, created_at, updated_at
      FROM ai_training_scenarios 
      WHERE business_id = $1 
      ORDER BY category, title
    `;
    
    const result = await db.query(query, [businessId]);
    res.json(result.rows);
  } catch (err) {
    console.error('Error fetching training scenarios:', err);
    res.status(500).json({ error: err.message });
  }
});

// Create new training scenario
router.post('/business/:businessId/scenarios', async (req, res) => {
  try {
    const { businessId } = req.params;
    const { title, description, category, user_input, expected_response, is_active = true } = req.body;

    const query = `
      INSERT INTO ai_training_scenarios 
      (business_id, title, description, category, user_input, expected_response, is_active)
      VALUES ($1, $2, $3, $4, $5, $6, $7)
      RETURNING *
    `;
    
    const result = await db.query(query, [
      businessId, title, description, category, user_input, expected_response, is_active
    ]);
    
    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error('Error creating training scenario:', err);
    res.status(500).json({ error: err.message });
  }
});

// Update training scenario
router.put('/business/:businessId/scenarios/:scenarioId', async (req, res) => {
  try {
    const { businessId, scenarioId } = req.params;
    const { title, description, category, user_input, expected_response, is_active } = req.body;

    const query = `
      UPDATE ai_training_scenarios 
      SET title = $1, description = $2, category = $3, user_input = $4, 
          expected_response = $5, is_active = $6, updated_at = CURRENT_TIMESTAMP
      WHERE id = $7 AND business_id = $8
      RETURNING *
    `;
    
    const result = await db.query(query, [
      title, description, category, user_input, expected_response, is_active, scenarioId, businessId
    ]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Training scenario not found' });
    }
    
    res.json(result.rows[0]);
  } catch (err) {
    console.error('Error updating training scenario:', err);
    res.status(500).json({ error: err.message });
  }
});

// Delete training scenario
router.delete('/business/:businessId/scenarios/:scenarioId', async (req, res) => {
  try {
    const { businessId, scenarioId } = req.params;

    const query = 'DELETE FROM ai_training_scenarios WHERE id = $1 AND business_id = $2 RETURNING id';
    const result = await db.query(query, [scenarioId, businessId]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Training scenario not found' });
    }
    
    res.json({ message: 'Training scenario deleted successfully' });
  } catch (err) {
    console.error('Error deleting training scenario:', err);
    res.status(500).json({ error: err.message });
  }
});

// Test AI response for a scenario
router.post('/business/:businessId/test-response', async (req, res) => {
  try {
    const { businessId } = req.params;
    const { user_input, scenario_id } = req.body;

    // This is where you'd integrate with your AI service (OpenRouter, etc.)
    // For now, we'll simulate a response
    const mockAiResponse = {
      response: "Thank you for calling! I'd be happy to help you with that request. Let me check our availability.",
      confidence: 0.85,
      intent: "appointment_booking",
      entities: {
        service_type: "consultation",
        preferred_time: "afternoon"
      }
    };

    // If scenario_id is provided, update the last_tested timestamp
    if (scenario_id) {
      await db.query(
        'UPDATE ai_training_scenarios SET last_tested = CURRENT_TIMESTAMP WHERE id = $1 AND business_id = $2',
        [scenario_id, businessId]
      );
    }

    // Log the test for analytics
    await db.query(
      `INSERT INTO system_logs (level, message, service, business_id, metadata) 
       VALUES ('info', 'AI response tested', 'ai-training', $1, $2)`,
      [businessId, JSON.stringify({ user_input, scenario_id, response: mockAiResponse })]
    );

    res.json(mockAiResponse);
  } catch (err) {
    console.error('Error testing AI response:', err);
    res.status(500).json({ error: err.message });
  }
});

// Get scenario analytics
router.get('/business/:businessId/scenarios/analytics', async (req, res) => {
  try {
    const { businessId } = req.params;

    const query = `
      SELECT 
        category,
        COUNT(*) as total_scenarios,
        COUNT(CASE WHEN is_active = true THEN 1 END) as active_scenarios,
        AVG(success_rate) as avg_success_rate,
        COUNT(CASE WHEN last_tested IS NOT NULL THEN 1 END) as tested_scenarios
      FROM ai_training_scenarios 
      WHERE business_id = $1 
      GROUP BY category
      ORDER BY category
    `;
    
    const result = await db.query(query, [businessId]);
    
    // Get recent testing activity
    const recentTestsQuery = `
      SELECT created_at, metadata->>'scenario_id' as scenario_id, metadata->>'user_input' as user_input
      FROM system_logs 
      WHERE business_id = $1 AND service = 'ai-training' 
      ORDER BY created_at DESC 
      LIMIT 10
    `;
    const recentTests = await db.query(recentTestsQuery, [businessId]);

    res.json({
      categoryStats: result.rows,
      recentTests: recentTests.rows,
      totalScenarios: result.rows.reduce((sum, row) => sum + parseInt(row.total_scenarios), 0)
    });
  } catch (err) {
    console.error('Error fetching scenario analytics:', err);
    res.status(500).json({ error: err.message });
  }
});

// Bulk import scenarios
router.post('/business/:businessId/scenarios/bulk-import', async (req, res) => {
  try {
    const { businessId } = req.params;
    const { scenarios } = req.body;

    const results = [];
    
    for (const scenario of scenarios) {
      const query = `
        INSERT INTO ai_training_scenarios 
        (business_id, title, description, category, user_input, expected_response, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id, title
      `;
      
      const result = await db.query(query, [
        businessId,
        scenario.title,
        scenario.description,
        scenario.category,
        scenario.user_input,
        scenario.expected_response,
        scenario.is_active !== undefined ? scenario.is_active : true
      ]);
      
      results.push(result.rows[0]);
    }

    res.status(201).json({
      message: `${results.length} scenarios imported successfully`,
      scenarios: results
    });
  } catch (err) {
    console.error('Error bulk importing scenarios:', err);
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;