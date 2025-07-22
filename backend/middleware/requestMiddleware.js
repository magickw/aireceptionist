const { v4: uuidv4 } = require('uuid');
const logger = require('../utils/logger');

// Request ID middleware for tracking requests
const requestId = (req, res, next) => {
  req.id = req.headers['x-request-id'] || uuidv4();
  res.set('X-Request-ID', req.id);
  next();
};

// Request logging middleware
const requestLogger = (req, res, next) => {
  const startTime = Date.now();

  // Override res.end to log response
  const originalEnd = res.end;
  res.end = function(...args) {
    const responseTime = Date.now() - startTime;
    logger.logRequest(req, res, responseTime);
    originalEnd.apply(this, args);
  };

  next();
};

// Rate limiting middleware
const rateLimit = require('express-rate-limit');

const createRateLimit = (windowMs, max, message) => {
  return rateLimit({
    windowMs,
    max,
    message: {
      status: 'error',
      message
    },
    standardHeaders: true,
    legacyHeaders: false,
    handler: (req, res) => {
      logger.warn('Rate limit exceeded', {
        ip: req.ip,
        url: req.originalUrl,
        method: req.method,
        requestId: req.id
      });
      
      res.status(429).json({
        status: 'error',
        message: 'Too many requests, please try again later.',
        requestId: req.id
      });
    }
  });
};

// Different rate limits for different endpoints
const apiLimiter = createRateLimit(
  15 * 60 * 1000, // 15 minutes
  100, // limit each IP to 100 requests per windowMs
  'Too many requests from this IP, please try again later.'
);

const authLimiter = createRateLimit(
  15 * 60 * 1000, // 15 minutes
  5, // limit each IP to 5 requests per windowMs
  'Too many login attempts from this IP, please try again later.'
);

module.exports = {
  requestId,
  requestLogger,
  apiLimiter,
  authLimiter
};