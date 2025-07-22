const request = require('supertest');
const app = require('../index');
const db = require('../database');

describe('Authentication API', () => {
  let userToken;
  let testUserId;

  beforeAll(async () => {
    // Clean up test data
    await db.query("DELETE FROM users WHERE email LIKE '%test%'");
  });

  afterAll(async () => {
    // Clean up test data
    await db.query("DELETE FROM users WHERE email LIKE '%test%'");
    await db.end();
  });

  describe('POST /api/auth/signup', () => {
    it('should create a new user successfully', async () => {
      const userData = {
        name: 'Test User',
        email: 'test@example.com',
        password: 'testpassword123',
        passwordConfirm: 'testpassword123'
      };

      const res = await request(app)
        .post('/api/auth/signup')
        .send(userData)
        .expect(201);

      expect(res.body.status).toBe('success');
      expect(res.body.token).toBeDefined();
      expect(res.body.data.user.email).toBe(userData.email);
      expect(res.body.data.user.password).toBeUndefined();

      userToken = res.body.token;
      testUserId = res.body.data.user.id;
    });

    it('should fail with invalid email', async () => {
      const userData = {
        name: 'Test User',
        email: 'invalid-email',
        password: 'testpassword123',
        passwordConfirm: 'testpassword123'
      };

      const res = await request(app)
        .post('/api/auth/signup')
        .send(userData)
        .expect(400);

      expect(res.body.status).toBe('fail');
      expect(res.body.message).toContain('valid email');
    });

    it('should fail with weak password', async () => {
      const userData = {
        name: 'Test User',
        email: 'test2@example.com',
        password: '123',
        passwordConfirm: '123'
      };

      const res = await request(app)
        .post('/api/auth/signup')
        .send(userData)
        .expect(400);

      expect(res.body.message).toContain('8 characters');
    });

    it('should fail with mismatched passwords', async () => {
      const userData = {
        name: 'Test User',
        email: 'test3@example.com',
        password: 'testpassword123',
        passwordConfirm: 'differentpassword'
      };

      const res = await request(app)
        .post('/api/auth/signup')
        .send(userData)
        .expect(400);

      expect(res.body.message).toContain('do not match');
    });

    it('should fail with duplicate email', async () => {
      const userData = {
        name: 'Test User 2',
        email: 'test@example.com', // Same email as first test
        password: 'testpassword123',
        passwordConfirm: 'testpassword123'
      };

      const res = await request(app)
        .post('/api/auth/signup')
        .send(userData)
        .expect(400);

      expect(res.body.message).toContain('already exists');
    });
  });

  describe('POST /api/auth/login', () => {
    it('should login successfully with correct credentials', async () => {
      const loginData = {
        email: 'test@example.com',
        password: 'testpassword123'
      };

      const res = await request(app)
        .post('/api/auth/login')
        .send(loginData)
        .expect(200);

      expect(res.body.status).toBe('success');
      expect(res.body.token).toBeDefined();
      expect(res.body.data.user.email).toBe(loginData.email);
    });

    it('should fail with incorrect password', async () => {
      const loginData = {
        email: 'test@example.com',
        password: 'wrongpassword'
      };

      const res = await request(app)
        .post('/api/auth/login')
        .send(loginData)
        .expect(401);

      expect(res.body.message).toContain('Incorrect email or password');
    });

    it('should fail with non-existent email', async () => {
      const loginData = {
        email: 'nonexistent@example.com',
        password: 'testpassword123'
      };

      const res = await request(app)
        .post('/api/auth/login')
        .send(loginData)
        .expect(401);

      expect(res.body.message).toContain('Incorrect email or password');
    });

    it('should fail without email and password', async () => {
      const res = await request(app)
        .post('/api/auth/login')
        .send({})
        .expect(400);

      expect(res.body.message).toContain('email and password');
    });
  });

  describe('Protected Routes', () => {
    it('should access protected route with valid token', async () => {
      const res = await request(app)
        .get('/api/businesses')
        .set('Authorization', `Bearer ${userToken}`)
        .expect(200);
    });

    it('should fail to access protected route without token', async () => {
      const res = await request(app)
        .get('/api/businesses')
        .expect(401);

      expect(res.body.message).toContain('not logged in');
    });

    it('should fail with invalid token', async () => {
      const res = await request(app)
        .get('/api/businesses')
        .set('Authorization', 'Bearer invalid-token')
        .expect(401);

      expect(res.body.message).toContain('Invalid token');
    });
  });

  describe('POST /api/auth/logout', () => {
    it('should logout successfully', async () => {
      const res = await request(app)
        .post('/api/auth/logout')
        .expect(200);

      expect(res.body.status).toBe('success');
      expect(res.body.message).toBe('Logged out successfully');
    });
  });
});