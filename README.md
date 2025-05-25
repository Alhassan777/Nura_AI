# Nura - Mental Health AI Assistant

A comprehensive mental health AI assistant with separated frontend and backend architecture for optimal development and deployment.

## 🏗️ Architecture

This project is now separated into two main components:

### Frontend (`/frontend`)

- **Technology**: Next.js 14 with TypeScript
- **Port**: 3000
- **Features**:
  - Modern React-based chat interface
  - Real-time health monitoring
  - Crisis detection indicators
  - Memory storage status
  - Test scenarios and system information

### Backend (`/backend`)

- **Technology**: Python FastAPI with AI/ML services
- **Port**: 8000
- **Features**:
  - Mental health assistant with Gemini AI
  - Vector-based memory storage (Pinecone)
  - Crisis detection and scoring
  - Comprehensive conversation analysis
  - Redis caching and session management

## 🚀 Quick Start

### Option 1: Start Both Services Together

```bash
./start-both.sh
```

### Option 2: Start Services Separately

#### Backend Only

```bash
cd backend
./start-backend.sh
```

#### Frontend Only

```bash
cd frontend
./start-frontend.sh
```

## 📋 Prerequisites

### Backend Requirements

- Python 3.8+
- Redis server
- Google AI API key
- Pinecone account (optional)

### Frontend Requirements

- Node.js 18+
- npm or yarn

## ⚙️ Configuration

### Backend Configuration (`backend/.env`)

```bash
# Google AI Configuration
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_CLOUD_PROJECT=your-google-cloud-project

# Model Configuration
GEMINI_MODEL=gemini-pro
GEMINI_EMBEDDING_MODEL=gemini-pro

# Memory Service Configuration
MEMORY_SERVICE_PORT=8000

# Vector Database Configuration
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=nura-memory

# Redis Configuration
REDIS_URL=redis://localhost:6379
```

### Frontend Configuration (`frontend/.env.local`)

```bash
# Backend URL
BACKEND_URL=http://localhost:8000

# Auth0 Configuration (optional)
AUTH0_SECRET=your-auth0-secret-here
AUTH0_BASE_URL=http://localhost:3000
AUTH0_ISSUER_BASE_URL=https://your-domain.auth0.com
```

## 🛠️ Development Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env
# Edit .env with your configuration

# Start Redis
redis-server --daemonize yes

# Start backend
./start-backend.sh
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.local.example .env.local
# Edit .env.local with your configuration

# Start frontend
./start-frontend.sh
```

## 🧪 Testing

### Test Chat Interface

Visit `http://localhost:3000/test-chat` for a comprehensive testing interface that includes:

- Real-time chat with the AI assistant
- Health status monitoring
- Crisis level indicators
- Memory storage confirmation
- Configuration warnings
- Suggested test scenarios

### API Testing

- Backend API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Frontend API: `http://localhost:3000/api/chat`

## 📁 Project Structure

```
nura-app/
├── frontend/                 # Next.js Frontend
│   ├── src/
│   │   ├── app/             # Next.js App Router
│   │   ├── components/      # React Components
│   │   ├── lib/            # Utilities
│   │   └── utils/          # Helper functions
│   ├── public/             # Static assets
│   ├── package.json        # Frontend dependencies
│   ├── .env.local          # Frontend environment
│   └── start-frontend.sh   # Frontend startup script
│
├── backend/                 # Python Backend
│   ├── services/           # Core services
│   │   └── memory/         # Memory service
│   │       ├── api.py      # FastAPI application
│   │       ├── assistant/  # AI assistant
│   │       ├── storage/    # Vector storage
│   │       ├── scoring/    # Memory scoring
│   │       └── prompts/    # AI prompts
│   ├── data/              # Data storage
│   ├── logs/              # Application logs
│   ├── myenv/             # Python virtual environment
│   ├── requirements.txt   # Python dependencies
│   ├── .env              # Backend environment
│   └── start-backend.sh  # Backend startup script
│
├── start-both.sh          # Start both services
└── README.md             # This file
```

## 🔧 Benefits of Separation

### Development Benefits

- **Independent Development**: Frontend and backend teams can work independently
- **Faster Compilation**: Frontend builds don't wait for Python dependencies
- **Technology Flexibility**: Each service can use optimal technologies
- **Easier Testing**: Services can be tested in isolation

### Deployment Benefits

- **Scalability**: Services can be scaled independently
- **Container-Ready**: Each service can be containerized separately
- **Cloud Deployment**: Can deploy to different cloud services
- **Load Balancing**: Frontend and backend can have different load balancing strategies

### Maintenance Benefits

- **Clear Separation of Concerns**: Frontend handles UI, backend handles AI/ML
- **Independent Updates**: Services can be updated without affecting each other
- **Easier Debugging**: Issues can be isolated to specific services
- **Better Resource Management**: Each service can have optimized resource allocation

## 🚀 Production Deployment

### Docker Deployment (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Manual Deployment

1. Deploy backend to a Python hosting service (e.g., Railway, Heroku, AWS)
2. Deploy frontend to a static hosting service (e.g., Vercel, Netlify)
3. Update `BACKEND_URL` in frontend environment to point to deployed backend

## 📚 Documentation

- [Memory Setup Guide](backend/MEMORY_SETUP_GUIDE.md)
- [Vector Database Setup](backend/VECTOR_DB_SETUP_GUIDE.md)
- [Pinecone Setup Guide](backend/PINECONE_SETUP_GUIDE.md)
- [Testing Guide](backend/README_TESTING.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes in appropriate frontend or backend directory
4. Test both services independently
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
