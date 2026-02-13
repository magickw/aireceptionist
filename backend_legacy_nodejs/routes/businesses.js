const express = require('express');
const router = express.Router();
const db = require('../database');

// Get all businesses
router.get('/', async (req, res) => {
  try {
    const { rows } = await db.query('SELECT * FROM businesses');
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get a single business by id
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { rows } = await db.query('SELECT * FROM businesses WHERE id = $1', [id]);
    if (rows.length === 0) {
      return res.status(404).json({ error: 'Business not found' });
    }
    res.json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Create a new business
router.post('/', async (req, res) => {
  try {
    const { name, type, settings, operating_hours } = req.body;
    const { rows } = await db.query(
      'INSERT INTO businesses (name, type, settings, operating_hours) VALUES ($1, $2, $3, $4) RETURNING *',
      [name, type, settings, operating_hours]
    );
    res.status(201).json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update a business
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { name, type, settings, operating_hours } = req.body;
    const { rows } = await db.query(
      'UPDATE businesses SET name = $1, type = $2, settings = $3, operating_hours = $4 WHERE id = $5 RETURNING *',
      [name, type, settings, operating_hours, id]
    );
    if (rows.length === 0) {
      return res.status(404).json({ error: 'Business not found' });
    }
    res.json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Delete a business
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { rowCount } = await db.query('DELETE FROM businesses WHERE id = $1', [id]);
    if (rowCount === 0) {
      return res.status(404).json({ error: 'Business not found' });
    }
    res.status(204).send();
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
