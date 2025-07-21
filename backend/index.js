const express = require('express');
const app = express();
const port = process.env.PORT || 3001;
const db = require('./database.js');

app.get('/api/businesses', (req, res) => {
  db.all('SELECT * FROM businesses', [], (err, rows) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json({ businesses: rows });
  });
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
