const express = require('express');
const authService = require('../services/authService');
const { AppError } = require('../middleware/errorHandler');
const { authLimiter } = require('../middleware/requestMiddleware');
const logger = require('../utils/logger');
const db = require('../database');
const router = express.Router();

// Input validation
const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const validatePassword = (password) => {
  return password && password.length >= 8;
};

// Sign up
router.post('/signup', authLimiter, async (req, res, next) => {
  try {
    const { name, email, password, passwordConfirm, role = 'business_owner' } = req.body;

    // Validation
    if (!name || !email || !password) {
      return next(new AppError('Please provide name, email, and password', 400));
    }

    if (!validateEmail(email)) {
      return next(new AppError('Please provide a valid email', 400));
    }

    if (!validatePassword(password)) {
      return next(new AppError('Password must be at least 8 characters long', 400));
    }

    if (password !== passwordConfirm) {
      return next(new AppError('Passwords do not match', 400));
    }

    // Check if user already exists
    const existingUser = await db.query('SELECT id FROM users WHERE email = $1', [email]);
    if (existingUser.rows.length > 0) {
      return next(new AppError('User with this email already exists', 400));
    }

    // Hash password
    const hashedPassword = await authService.hashPassword(password);

    // Create user
    const { rows } = await db.query(
      'INSERT INTO users (name, email, password, role, created_at) VALUES ($1, $2, $3, $4, NOW()) RETURNING id, name, email, role, created_at',
      [name, email, hashedPassword, role]
    );

    const newUser = rows[0];

    logger.logBusinessOperation('user_registration', {
      userId: newUser.id,
      email: newUser.email,
      role: newUser.role
    });

    // Send token
    authService.createSendToken(newUser, 201, res, 'User registered successfully');
  } catch (error) {
    logger.error('Signup error:', error);
    return next(new AppError('Registration failed', 500));
  }
});

// Login
router.post('/login', authLimiter, async (req, res, next) => {
  try {
    const { email, password } = req.body;

    // Check if email and password exist
    if (!email || !password) {
      return next(new AppError('Please provide email and password', 400));
    }

    // Check if user exists and password is correct
    const { rows } = await db.query('SELECT * FROM users WHERE email = $1', [email]);
    const user = rows[0];

    if (!user || !(await authService.comparePassword(password, user.password))) {
      logger.warn('Failed login attempt', {
        email,
        ip: req.ip,
        userAgent: req.get('User-Agent')
      });
      return next(new AppError('Incorrect email or password', 401));
    }

    // Check if user is active
    if (user.status === 'inactive') {
      return next(new AppError('Your account has been deactivated. Please contact support.', 401));
    }

    // Send token
    authService.createSendToken(user, 200, res, 'Logged in successfully');
  } catch (error) {
    logger.error('Login error:', error);
    return next(new AppError('Login failed', 500));
  }
});

// Logout
router.post('/logout', (req, res) => {
  res.cookie('jwt', 'loggedout', {
    expires: new Date(Date.now() + 10 * 1000),
    httpOnly: true
  });
  
  res.status(200).json({
    status: 'success',
    message: 'Logged out successfully'
  });
});

// Forgot password
router.post('/forgot-password', authLimiter, async (req, res, next) => {
  try {
    const { email } = req.body;

    if (!email) {
      return next(new AppError('Please provide your email address', 400));
    }

    // Get user based on email
    const { rows } = await db.query('SELECT * FROM users WHERE email = $1', [email]);
    const user = rows[0];

    if (!user) {
      return next(new AppError('There is no user with that email address', 404));
    }

    // Generate random reset token
    const { resetToken, passwordResetToken, passwordResetExpires } = 
      authService.generatePasswordResetToken();

    // Save token to database
    await db.query(
      'UPDATE users SET password_reset_token = $1, password_reset_expires = $2 WHERE id = $3',
      [passwordResetToken, new Date(passwordResetExpires), user.id]
    );

    logger.logBusinessOperation('password_reset_requested', {
      userId: user.id,
      email: user.email
    });

    // In a real app, send email here
    // For demo purposes, we'll just return success
    res.status(200).json({
      status: 'success',
      message: 'Password reset token sent to email',
      // In production, remove this line
      resetToken: process.env.NODE_ENV === 'development' ? resetToken : undefined
    });
  } catch (error) {
    logger.error('Forgot password error:', error);
    return next(new AppError('Failed to process password reset request', 500));
  }
});

// Reset password
router.patch('/reset-password/:token', async (req, res, next) => {
  try {
    const { password, passwordConfirm } = req.body;

    if (!password || !passwordConfirm) {
      return next(new AppError('Please provide password and password confirmation', 400));
    }

    if (!validatePassword(password)) {
      return next(new AppError('Password must be at least 8 characters long', 400));
    }

    if (password !== passwordConfirm) {
      return next(new AppError('Passwords do not match', 400));
    }

    // Get user based on token
    const hashedToken = require('crypto')
      .createHash('sha256')
      .update(req.params.token)
      .digest('hex');

    const { rows } = await db.query(
      'SELECT * FROM users WHERE password_reset_token = $1 AND password_reset_expires > $2',
      [hashedToken, new Date()]
    );

    const user = rows[0];
    if (!user) {
      return next(new AppError('Token is invalid or has expired', 400));
    }

    // Update password
    const hashedPassword = await authService.hashPassword(password);
    await db.query(
      'UPDATE users SET password = $1, password_reset_token = NULL, password_reset_expires = NULL, password_changed_at = NOW() WHERE id = $2',
      [hashedPassword, user.id]
    );

    logger.logBusinessOperation('password_reset_completed', {
      userId: user.id,
      email: user.email
    });

    // Log user in
    authService.createSendToken(user, 200, res, 'Password reset successfully');
  } catch (error) {
    logger.error('Reset password error:', error);
    return next(new AppError('Failed to reset password', 500));
  }
});

module.exports = router;