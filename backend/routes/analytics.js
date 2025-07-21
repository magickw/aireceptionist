const express = require('express');
const router = express.Router();
const db = require('../database');

// Get call analytics for a business
router.get('/business/:businessId', async (req, res) => {
  try {
    const { businessId } = req.params;

    // Total calls
    const totalCalls = await db.query('SELECT COUNT(*) FROM call_logs WHERE business_id = $1', [businessId]);

    // Average call duration (placeholder, as we don't store duration yet)
    const avgCallDuration = 0; 

    // Appointments booked
    const appointmentsBooked = await db.query('SELECT COUNT(*) FROM appointments WHERE business_id = $1 AND status = $2', [businessId, 'confirmed']);

    res.json({
      totalCalls: totalCalls.rows[0].count,
      avgCallDuration: avgCallDuration,
      appointmentsBooked: appointmentsBooked.rows[0].count,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
