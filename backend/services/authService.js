const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { AppError } = require('../middleware/errorHandler');
const logger = require('../utils/logger');

class AuthService {
  constructor() {
    this.jwtSecret = process.env.JWT_SECRET || 'your-super-secret-jwt-key';
    this.jwtExpiresIn = process.env.JWT_EXPIRES_IN || '30d';
    this.bcryptSaltRounds = 12;
  }

  // Generate JWT token
  signToken(id, role = 'user') {
    return jwt.sign({ id, role }, this.jwtSecret, {
      expiresIn: this.jwtExpiresIn,
      issuer: 'ai-receptionist',
      audience: 'ai-receptionist-app'
    });
  }

  // Verify JWT token
  verifyToken(token) {
    return jwt.verify(token, this.jwtSecret, {
      issuer: 'ai-receptionist',
      audience: 'ai-receptionist-app'
    });
  }

  // Hash password
  async hashPassword(password) {
    return await bcrypt.hash(password, this.bcryptSaltRounds);
  }

  // Compare password
  async comparePassword(candidatePassword, userPassword) {
    return await bcrypt.compare(candidatePassword, userPassword);
  }

  // Create and send token response
  createSendToken(user, statusCode, res, message = 'Success') {
    const token = this.signToken(user.id, user.role);
    
    const cookieOptions = {
      expires: new Date(
        Date.now() + process.env.JWT_COOKIE_EXPIRES_IN * 24 * 60 * 60 * 1000
      ),
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict'
    };

    res.cookie('jwt', token, cookieOptions);

    // Remove password from output
    user.password = undefined;

    logger.logBusinessOperation('user_login', {
      userId: user.id,
      email: user.email,
      role: user.role
    });

    res.status(statusCode).json({
      status: 'success',
      message,
      token,
      data: {
        user
      }
    });
  }

  // Generate password reset token
  generatePasswordResetToken() {
    const resetToken = require('crypto').randomBytes(32).toString('hex');
    const passwordResetToken = require('crypto')
      .createHash('sha256')
      .update(resetToken)
      .digest('hex');

    const passwordResetExpires = Date.now() + 10 * 60 * 1000; // 10 minutes

    return {
      resetToken,
      passwordResetToken,
      passwordResetExpires
    };
  }
}

module.exports = new AuthService();