const express = require('express');
const router = express.Router();
const db = require('../database');

// Get all appointments for a business
router.get('/business/:businessId', async (req, res) => {
  try {
    const { businessId } = req.params;
    const { rows } = await db.query('SELECT * FROM appointments WHERE business_id = $1', [businessId]);
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get a single appointment by id
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { rows } = await db.query('SELECT * FROM appointments WHERE id = $1', [id]);
    if (rows.length === 0) {
      return res.status(404).json({ error: 'Appointment not found' });
    }
    res.json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Create a new appointment
router.post('/', async (req, res) => {
  try {
    const { business_id, customer_name, customer_phone, appointment_time, service_type } = req.body;
    const { rows } = await db.query(
      'INSERT INTO appointments (business_id, customer_name, customer_phone, appointment_time, service_type) VALUES ($1, $2, $3, $4, $5) RETURNING *',
      [business_id, customer_name, customer_phone, appointment_time, service_type]
    );
    res.status(201).json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update an appointment
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { customer_name, customer_phone, appointment_time, service_type, status } = req.body;
    const { rows } = await db.query(
      'UPDATE appointments SET customer_name = $1, customer_phone = $2, appointment_time = $3, service_type = $4, status = $5 WHERE id = $6 RETURNING *',
      [customer_name, customer_phone, appointment_time, service_type, status, id]
    );
    if (rows.length === 0) {
      return res.status(404).json({ error: 'Appointment not found' });
    }
    res.json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Delete an appointment
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { rowCount } = await db.query('DELETE FROM appointments WHERE id = $1', [id]);
    if (rowCount === 0) {
      return res.status(404).json({ error: 'Appointment not found' });
    }
    res.status(204).send();
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
