const { Pool } = require('pg');

const pool = new Pool({
  user: 'user',
  host: 'localhost',
  database: 'aireceptionist',
  password: 'password',
  port: 5435,
});

module.exports = {
  query: (text, params) => pool.query(text, params),
};
