const express = require('express');
const router = express.Router();
const db = require('../database');

// Get all call logs for a business
router.get('/business/:businessId', async (req, res) => {
  try {
    const { businessId } = req.params;
    const { rows } = await db.query('SELECT * FROM call_logs WHERE business_id = $1', [businessId]);
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get a single call log by id
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { rows } = await db.query('SELECT * FROM call_logs WHERE id = $1', [id]);
    if (rows.length === 0) {
      return res.status(404).json({ error: 'Call log not found' });
    }
    res.json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Create a new call log (this will primarily be done by the Twilio webhook)
router.post('/', async (req, res) => {
  try {
    const { business_id, customer_phone, call_sid, transcript, recording_url } = req.body;
    const { rows } = await db.query(
      'INSERT INTO call_logs (business_id, customer_phone, call_sid, transcript, recording_url) VALUES ($1, $2, $3, $4, $5) RETURNING *',
      [business_id, customer_phone, call_sid, transcript, recording_url]
    );
    res.status(201).json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;