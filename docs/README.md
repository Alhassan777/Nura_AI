# Nura - Mental Health AI Assistant

A comprehensive mental health AI assistant with separated frontend and backend architecture for optimal development and deployment.

## 🏗️ Architecture

This project is now separated into two main components:

### Frontend (`/nura-fe`)

- **Technology**: Next.js 15.3.2 with React 19 and TypeScript 5
- **Port**: 3000
- **Features**:
  - Modern React-based chat interface with AI assistant
  - Real-time health monitoring and memory management
  - Gamification system with badges and progress tracking
  - Safety network for connecting with trusted contacts
  - Calendar integration for mood and reflection tracking
  - Crisis detection indicators and privacy controls
  - Image generation capabilities

📖 **Frontend Documentation**: See [`FRONTEND_COMPREHENSIVE_GUIDE.md`](./FRONTEND_COMPREHENSIVE_GUIDE.md) for complete development guide

🔌 **API Integration**: See [`FRONTEND_API_QUICK_REFERENCE.md`](./FRONTEND_API_QUICK_REFERENCE.md) for backend connection details

### Backend (`/backend`)

- **Technology**: Python FastAPI with AI/ML services
- **Port**: 8000
- **Features**:
  - **🧠 Refactored Mental Health Assistant** - Modular architecture with specialized extractors
  - Vector-based memory storage (ChromaDB/Pinecone)
  - Crisis detection and intervention system
  - Action plan generation for emotional and personal goals
  - Schedule extraction for wellness check-ins
  - Image generation with FLUX.1-dev
  - Comprehensive conversation analysis
  - Redis caching and session management
  - Privacy and GDPR compliance
  - Safety network and gamification services

## 🚀 Quick Start

### Option 1: Start Both Services Together

```bash
./scripts/start-both.sh
```

### Option 2: Start Services Separately

#### Backend Only

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Frontend Only

```bash
cd nura-fe
npm run dev
```

## 📋 Prerequisites

### Backend Requirements

- Python 3.8+
- Redis server
- Google AI API key
- Pinecone account (optional, ChromaDB by default)
- Hugging Face API key (for image generation)

### Frontend Requirements

- Node.js 18+
- npm or yarn
- Supabase account for authentication

## ⚙️ Configuration

### Backend Configuration (`backend/.env`)

```bash
# Google AI Configuration
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_CLOUD_PROJECT=your-google-cloud-project

# Model Configuration
GEMINI_MODEL=gemini-pro
GEMINI_EMBEDDING_MODEL=embedding-001

# Memory Service Configuration
MEMORY_SERVICE_PORT=8000

# Vector Database Configuration (ChromaDB is default)
USE_PINECONE=false
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=nura-memory
CHROMA_PERSIST_DIR=./chroma

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Image Generation Configuration
HF_TOKEN=your-hugging-face-token
```

### Frontend Configuration (`nura-fe/.env.local`)

```bash
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key

# Optional: Development flags
NODE_ENV=development
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

# Setup database schemas
python scripts/setup_image_generation_db.py

# Start Redis
redis-server --daemonize yes

# Start backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd nura-fe

# Install dependencies
npm install

# Copy environment template
cp .env.local.example .env.local
# Edit .env.local with your configuration

# Start frontend
npm run dev
```

📖 **Detailed Setup Guide**: See [`FRONTEND_COMPREHENSIVE_GUIDE.md`](./FRONTEND_COMPREHENSIVE_GUIDE.md) for complete frontend setup instructions.

## 🧪 Testing

### Comprehensive Testing

Run the comprehensive test suite:

```bash
# Test refactored mental health assistant
python test_comprehensive_refactored_assistant.py

# Run all tests
python scripts/fix_all_tests.py

# Test image generation pipeline
python tests/test_actual_image_generation.py

# Test privacy systems
python scripts/run_privacy_test.py

# Check database schemas
python scripts/check_schema.py
```

### Application Testing

- **Frontend**: `http://localhost:3000` - Full application interface
- **Chat Interface**: `http://localhost:3000/chat` - AI assistant chat
- **Backend API**: `http://localhost:8000/docs` - API documentation
- **Health Check**: `http://localhost:8000/health` - System status

## 📁 Project Structure

```
nura-app/
├── docs/                    # Documentation
│   ├── README.md           # This file
│   ├── FRONTEND_COMPREHENSIVE_GUIDE.md  # Complete frontend development guide
│   ├── FRONTEND_API_QUICK_REFERENCE.md  # API integration reference
│   ├── SYSTEM_STATUS_SUMMARY.md         # Current system status and achievements
│   ├── DATABASE_*.md       # Database documentation
│   ├── IMAGE_GENERATION_*.md # Image generation docs
│   ├── PRIVACY_*.md        # Privacy documentation
│   └── SAFETY_*.md         # Safety feature docs
│
├── scripts/                 # Utility scripts
│   ├── start-both.sh       # Start both services
│   ├── setup_image_generation_db.py # DB setup
│   ├── check_schema.py     # Schema validation
│   └── fix_all_tests.py    # Test runner
│
├── tests/                   # Test files
│   ├── backend/            # Backend tests
│   ├── frontend/           # Frontend tests
│   ├── integration/        # Integration tests
│   ├── test_*.py          # Specific test files
│   └── COMPREHENSIVE_TEST_PLAN.md
│
├── logs/                    # Application logs
│   └── audit/              # Audit logs
│
├── nura-fe/                 # Next.js Frontend
│   ├── src/
│   │   ├── app/             # Next.js App Router (pages)
│   │   ├── components/      # React Components
│   │   │   ├── auth/        # Authentication components
│   │   │   ├── chat-components/ # Chat interface
│   │   │   ├── ui/          # ShadCN UI components
│   │   │   └── */           # Feature-specific components
│   │   ├── contexts/        # React Context providers
│   │   ├── services/        # API integration layer
│   │   │   ├── apis/        # API client functions
│   │   │   └── hooks/       # TanStack Query hooks
│   │   ├── lib/            # Utilities
│   │   └── utils/          # Helper functions
│   ├── public/             # Static assets
│   └── package.json        # Frontend dependencies
│
├── backend/                 # Python Backend
│   ├── services/           # Core services
│   │   ├── assistant/      # 🧠 REFACTORED Mental Health Assistant
│   │   │   ├── mental_health_assistant.py # Main assistant (refactored)
│   │   │   ├── extractors/ # Modular extraction components
│   │   │   │   ├── base_extractor.py     # Base patterns
│   │   │   │   ├── schedule_extractor.py # Schedule opportunities
│   │   │   │   ├── action_plan_extractor.py # Action plan generation
│   │   │   │   └── __init__.py           # Unified imports
│   │   │   └── crisis_intervention.py   # Crisis management
│   │   ├── memory/         # Memory service
│   │   │   ├── storage/    # Memory storage classes
│   │   │   │   ├── redis_store.py
│   │   │   │   └── vector_store.py
│   │   │   ├── memoryService.py # Main service
│   │   │   └── retrieval_processor.py
│   │   ├── image_generation/ # Image generation
│   │   ├── privacy/        # Privacy and GDPR
│   │   ├── chat/          # Chat service
│   │   ├── user/          # User management
│   │   ├── gamification/  # Badges and achievements
│   │   ├── safety_network/ # Safety features
│   │   ├── voice/         # Voice services
│   │   └── scheduling/    # Calendar and scheduling
│   ├── utils/             # Shared utilities
│   ├── models/            # Database models
│   ├── main.py           # FastAPI application entry
│   └── requirements.txt   # Python dependencies
│
├── chroma/                  # Vector database storage
├── docker-compose.yml      # Docker configuration
├── .gitignore             # Git ignore rules
└── yarn.lock              # Frontend dependencies lock
```

## 📚 Documentation Guide

### For Frontend Development

- **[Frontend Comprehensive Guide](./FRONTEND_COMPREHENSIVE_GUIDE.md)** - Complete development documentation
- **[Frontend API Quick Reference](./FRONTEND_API_QUICK_REFERENCE.md)** - Backend API integration guide

### For Backend Development

- **[System Status Summary](./SYSTEM_STATUS_SUMMARY.md)** - Current system achievements and architecture
- **[Database Documentation](./DATABASE_DOCUMENTATION.md)** - Database schema and architecture
- **[Image Generation Documentation](./IMAGE_GENERATION_DOCUMENTATION.md)** - Image generation service
- **[Voice Service Integration](./VOICE_SERVICE_INTEGRATION.md)** - Voice assistant features

### For System Administration

- **[Authentication Systems](./AUTHENTICATION_SYSTEMS.md)** - Auth architecture overview
- **[Chat Crisis Intervention Summary](./CHAT_CRISIS_INTERVENTION_SUMMARY.md)** - Crisis detection system

## 🔧 Recent Major Updates

- ✅ **🧠 Mental Health Assistant Refactoring**: Complete architectural overhaul

  - Reduced main assistant from 1,770 → 579 lines (67% reduction)
  - Created modular extractor system with specialized components
  - 90%+ functionality parity maintained with comprehensive testing
  - Eliminated 80% of code duplication through base classes
  - Added parallel processing for improved performance

- ✅ **Frontend Documentation**: Created comprehensive development guides
- ✅ **API Integration**: Documented all 12+ backend service endpoints
- ✅ **Component Patterns**: Established standardized development patterns
- ✅ **Authentication**: Supabase integration with JWT tokens
- ✅ **State Management**: React Query + Context API implementation
- ✅ **UI System**: ShadCN UI + Tailwind CSS + Ant Design
- ✅ **Safety Features**: Network invitations and emergency contacts
- ✅ **Gamification**: Badge system and progress tracking

## 🎯 Key Architectural Improvements

### **Modular Mental Health Assistant**

```
Before: 1,770-line monolithic file
After:  Modular architecture with specialized extractors

mental_health_assistant.py (579 lines)
├── extractors/
│   ├── base_extractor.py           # Common patterns
│   ├── schedule_extractor.py       # Wellness check-ins
│   ├── action_plan_extractor.py    # Goal achievement
│   └── __init__.py                 # Unified imports
└── crisis_intervention.py          # Crisis management
```

### **Benefits Achieved**

- 🎯 **Maintainability**: Clear separation of concerns
- ⚡ **Performance**: Parallel processing of extractions
- 🧪 **Testability**: Independent extractor testing
- 📚 **Documentation**: Self-documenting modular code
- 🔄 **Extensibility**: Easy addition of new extractors

## 🚀 Getting Started

1. **New to the project?** Start with the [Frontend Comprehensive Guide](./FRONTEND_COMPREHENSIVE_GUIDE.md)
2. **Need API integration?** Check the [API Quick Reference](./FRONTEND_API_QUICK_REFERENCE.md)
3. **Understanding the system?** Review the [System Status Summary](./SYSTEM_STATUS_SUMMARY.md)
4. **Adding features?** Follow the patterns documented in the comprehensive guide
5. **Deploying?** Review the deployment section in the frontend guide

## 🔧 Benefits of Current Architecture

### Development Benefits

- **Independent Development**: Frontend and backend teams can work independently
- **Faster Compilation**: Frontend builds don't wait for Python dependencies
- **Technology Flexibility**: Each service can use optimal technologies
- **Easier Testing**: Services can be tested in isolation
- **Modular Backend**: Specialized components for different mental health features

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
- **Modular Components**: Mental health assistant features are independently maintainable

## 🚀 Production Deployment

### Docker Deployment (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Manual Deployment

1. Deploy backend to a Python hosting service (e.g., Railway, Heroku, AWS)
2. Deploy frontend to a static hosting service (e.g., Vercel, Netlify)
3. Update `NEXT_PUBLIC_API_URL` in frontend environment to point to deployed backend

## 📚 Documentation

- [System Status Summary](./SYSTEM_STATUS_SUMMARY.md) - Current achievements and architecture
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

**For Mental Health Assistant Changes**:

- Follow the modular extractor pattern
- Add tests for new extractors
- Maintain parallel processing compatibility

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
