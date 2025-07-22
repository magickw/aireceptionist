# AI Receptionist Pro

AI-powered business phone management platform with WebSocket, Authentication, and Comprehensive Logging.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v16 or higher)
- **npm** (v8 or higher)
- **PostgreSQL** (v13 or higher)

## 🚀 Getting Started

This project consists of two main components: a Next.js frontend and an Express.js backend. Each component has its own package.json and dependencies.

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd aireceptionist
```

2. **Install frontend dependencies**

```bash
cd frontend
npm install
```

3. **Install backend dependencies**

```bash
cd ../backend
npm install
```

### Configuration

1. **Set up environment variables**

Create `.env` files in both the frontend and backend directories based on the provided examples:

**Backend (.env)**
```
# Database
DATABASE_URL=postgres://username:password@localhost:5432/aireceptionist

# JWT Authentication
JWT_SECRET=your_jwt_secret_key
JWT_EXPIRES_IN=90d
JWT_COOKIE_EXPIRES_IN=90

# Server
PORT=3001
NODE_ENV=development

# External APIs
OPENROUTER_API_KEY=your_openrouter_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Logging
LOG_LEVEL=debug
```

**Frontend (.env.local)**
```
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=ws://localhost:3001/ws
```

2. **Set up the database**

Create a PostgreSQL database and run the schema file:

```bash
psql -U username -d aireceptionist -f backend/database/enhanced_schema.sql
```

### Running the Application

#### Development Mode

1. **Start the backend server**

```bash
cd backend
npm run dev
```

2. **Start the frontend development server**

```bash
# In a new terminal
cd frontend
npm run dev
```

#### Production Mode

1. **Build the frontend**

```bash
cd frontend
npm run build
```

2. **Start the backend server**

```bash
cd backend
npm start
```

3. **Start the frontend server**

```bash
cd frontend
npm start
```

## 🧪 Testing

```bash
cd backend
npm test
```

For coverage report:

```bash
cd backend
npm run test:coverage
```

## 📚 Documentation

For detailed implementation information, please refer to the [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) file.

## 🔒 Security Features

- JWT Authentication
- Password Hashing (bcrypt)
- CORS Protection
- Rate Limiting
- Input Validation
- HTTP Security Headers (Helmet.js)

## 📞 WebSocket Implementation

The application uses WebSockets for real-time communication during calls. See the WebSocket section in the Implementation Guide for details on message types and usage.

## 📊 Monitoring

A health endpoint is available at `/health` which provides system status information including:

- API Status
- Timestamp
- Uptime
- Memory Usage
- WebSocket Statistics

## 🤝 Contributing

Please read the [CONTRIBUTING.md](./CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.