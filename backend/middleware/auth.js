const authService = require('../services/authService');
const { AppError } = require('./errorHandler');
const logger = require('../utils/logger');
const db = require('../database');

// Protect routes - require authentication
const protect = async (req, res, next) => {
  try {
    // 1) Get token and check if it exists
    let token;
    if (
      req.headers.authorization &&
      req.headers.authorization.startsWith('Bearer')
    ) {
      token = req.headers.authorization.split(' ')[1];
    } else if (req.cookies.jwt) {
      token = req.cookies.jwt;
    }

    if (!token) {
      return next(
        new AppError('You are not logged in! Please log in to get access.', 401)
      );
    }

    // 2) Verify token
    let decoded;
    try {
      decoded = authService.verifyToken(token);
    } catch (error) {
      if (error.name === 'JsonWebTokenError') {
        return next(new AppError('Invalid token. Please log in again!', 401));
      } else if (error.name === 'TokenExpiredError') {
        return next(new AppError('Your token has expired! Please log in again.', 401));
      }
      return next(error);
    }

    // 3) Check if user still exists
    const { rows } = await db.query('SELECT * FROM users WHERE id = $1', [decoded.id]);
    if (rows.length === 0) {
      return next(
        new AppError('The user belonging to this token no longer exists.', 401)
      );
    }

    const currentUser = rows[0];

    // 4) Check if user changed password after the token was issued
    if (currentUser.password_changed_at) {
      const changedTimestamp = parseInt(
        new Date(currentUser.password_changed_at).getTime() / 1000,
        10
      );
      if (decoded.iat < changedTimestamp) {
        return next(
          new AppError('User recently changed password! Please log in again.', 401)
        );
      }
    }

    // Grant access to protected route
    req.user = currentUser;
    next();
  } catch (error) {
    logger.error('Authentication error:', error);
    return next(new AppError('Authentication failed', 401));
  }
};

// Restrict access to certain roles
const restrictTo = (...roles) => {
  return (req, res, next) => {
    if (!roles.includes(req.user.role)) {
      return next(
        new AppError('You do not have permission to perform this action', 403)
      );
    }
    next();
  };
};

// Check if user owns the resource
const checkOwnership = (resourceIdField = 'id') => {
  return async (req, res, next) => {
    try {
      const resourceId = req.params[resourceIdField];
      
      // Admin can access any resource
      if (req.user.role === 'admin') {
        return next();
      }

      // Business owners can only access their own resources
      if (req.user.role === 'business_owner') {
        const { rows } = await db.query(
          'SELECT user_id FROM businesses WHERE id = $1',
          [resourceId]
        );
        
        if (rows.length === 0 || rows[0].user_id !== req.user.id) {
          return next(
            new AppError('You can only access your own resources', 403)
          );
        }
      }

      next();
    } catch (error) {
      logger.error('Ownership check error:', error);
      return next(new AppError('Access check failed', 500));
    }
  };
};

// Optional authentication - doesn't fail if no token
const optionalAuth = async (req, res, next) => {
  try {
    let token;
    if (
      req.headers.authorization &&
      req.headers.authorization.startsWith('Bearer')
    ) {
      token = req.headers.authorization.split(' ')[1];
    } else if (req.cookies.jwt) {
      token = req.cookies.jwt;
    }

    if (!token) {
      return next();
    }

    // Verify token
    const decoded = authService.verifyToken(token);

    // Check if user still exists
    const { rows } = await db.query('SELECT * FROM users WHERE id = $1', [decoded.id]);
    if (rows.length > 0) {
      req.user = rows[0];
    }

    next();
  } catch (error) {
    // Silent fail for optional auth
    next();
  }
};

module.exports = {
  protect,
  restrictTo,
  checkOwnership,
  optionalAuth
};