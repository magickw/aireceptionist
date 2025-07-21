const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./database.db', (err) => {
  if (err) {
    console.error(err.message);
  }
  console.log('Connected to the SQLite database.');
});

db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- e.g., 'restaurant', 'spa', 'salon'
    settings TEXT
  )`);

  db.run(`CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER REFERENCES businesses(id),
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    appointment_time TEXT NOT NULL,
    service_type TEXT,
    status TEXT DEFAULT 'confirmed', -- e.g., 'confirmed', 'cancelled'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  )`);

  db.run(`CREATE TABLE IF NOT EXISTS call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER REFERENCES businesses(id),
    customer_phone TEXT NOT NULL,
    call_sid TEXT, -- from Twilio or other provider
    transcript TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  )`);
});

module.exports = db;
