# 🧠 Nura - Your AI Mental Health Companion

> **Nura** is a comprehensive, AI-powered mental health companion designed to provide personalized emotional support, memory management, crisis intervention, and wellness tracking through an intuitive chat and voice interface.

## 🌟 What is Nura?

Nura is an advanced mental health AI assistant that combines cutting-edge artificial intelligence with evidence-based therapeutic approaches to provide:

- **24/7 Emotional Support**: Always available for conversations, reflections, and guidance
- **Intelligent Memory System**: Remembers your experiences, preferences, and progress over time
- **Crisis Detection & Intervention**: Proactive identification of mental health crises with immediate support resources
- **Voice & Text Communication**: Seamless interaction through both text chat and voice conversations
- **Visual Emotional Expression**: AI-generated images to help visualize and process emotions
- **Gamified Wellness**: Progress tracking, badges, and achievements to motivate mental health practices
- **Safety Network**: Connect with trusted contacts for additional support when needed
- **Privacy-First Design**: Advanced PII detection and user-controlled data management

## 🏗️ Architecture

Nura is built with a modern, scalable architecture:

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│     Frontend        │    │      Backend        │    │   External APIs     │
│   (Next.js/React)   │◄──►│     (FastAPI)       │◄──►│  (Gemini, Vapi,     │
│     Port: 3000      │    │     Port: 8000      │    │   Hugging Face)     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                          │                          │
           ▼                          ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Authentication    │    │     Database        │    │   Vector Storage    │
│    (Supabase)       │    │    (Supabase)       │    │ (Pinecone/ChromaDB) │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## 🚀 Key Features

### 🧠 **Intelligent Conversations**

- Context-aware responses that remember your history
- Therapeutic conversation patterns based on evidence-based practices
- Emotion detection and appropriate response generation
- Crisis detection with immediate intervention protocols

### 💾 **Advanced Memory Management**

- **Short-term Memory**: Recent conversations and immediate context
- **Long-term Memory**: Persistent insights, preferences, and growth patterns
- **Emotional Anchors**: Significant memories that provide emotional grounding
- **Smart Relevance**: AI-powered memory retrieval based on current conversation context

### 🎤 **Voice Integration**

- Natural voice conversations through Vapi.ai integration
- Real-time emotion detection in voice tone
- Scheduled voice check-ins and reminders
- Phone and browser-based calling options

### 🎨 **Emotional Visualization**

- AI-generated images that represent your emotional state
- Visual therapy techniques through image analysis
- Mood boards and emotional journey visualization
- Custom image prompts based on therapeutic conversations

### 🏆 **Gamification & Progress**

- Achievement system with mental health milestones
- Progress tracking for various wellness metrics
- Badges for consistency, breakthrough moments, and growth
- Streak counters for daily check-ins and practices

### 🚨 **Crisis Support System**

- Real-time crisis detection through conversation analysis
- Immediate access to crisis resources and hotlines
- Emergency contact integration
- Escalation protocols for severe mental health episodes

### 🔒 **Privacy & Security**

- Advanced PII (Personally Identifiable Information) detection
- User-controlled data retention and deletion
- GDPR compliance and data protection
- Encrypted storage and secure communication

## 🛠️ Technology Stack

### Frontend

- **Framework**: Next.js 15.3.2 with React 19
- **Language**: TypeScript 5
- **UI Components**: ShadCN UI, Ant Design
- **Authentication**: Supabase Auth
- **State Management**: React Context API, React Query
- **Voice Integration**: Vapi.ai SDK

### Backend

- **Framework**: Python FastAPI
- **AI/ML**: Google Gemini AI, Hugging Face Transformers
- **Database**: Supabase (PostgreSQL)
- **Vector Storage**: Pinecone or ChromaDB
- **Caching**: Redis
- **Voice Services**: Vapi.ai
- **Image Generation**: FLUX.1-dev via Hugging Face

## 📋 Prerequisites

Before running Nura, ensure you have:

### System Requirements

- **Node.js** 18+ (for frontend)
- **Python** 3.8+ (for backend)
- **Redis** server (for caching)
- **Git** (for version control)

### Required API Keys & Services

- **Google AI API Key** (for Gemini AI) - [Get here](https://ai.google.dev/)
- **Supabase Account** (for database & auth) - [Sign up](https://supabase.com/)
- **Hugging Face Token** (for image generation) - [Get here](https://huggingface.co/settings/tokens)
- **Vapi.ai Account** (for voice features) - [Sign up](https://vapi.ai/)
- **Pinecone Account** (optional, for vector storage) - [Sign up](https://pinecone.io/)

## 🚀 Quick Start

### Option 1: Full Setup (Recommended)

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd nura-app
   ```

2. **Backend Setup**

   ```bash
   cd backend

   # Create virtual environment
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Setup environment
   cp .env.example .env
   # Edit .env with your API keys and configuration

   # Start Redis (if not running)
   redis-server --daemonize yes

   # Run database migrations (if needed)
   python scripts/setup_database.py

   # Start backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. **Frontend Setup** (in a new terminal)

   ```bash
   cd nura-fe

   # Install dependencies
   npm install

   # Setup environment
   cp .env.example .env.local
   # Edit .env.local with your configuration

   # Start frontend
   npm run dev
   ```

4. **Access the Application**
   - **Frontend**: http://localhost:3000
   - **Backend API Docs**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

### Option 2: Docker Setup (Coming Soon)

```bash
# Full docker-compose setup (in development)
docker-compose up -d
```

## ⚙️ Configuration

### Backend Configuration (`backend/.env`)

```bash
# Essential Configuration
GOOGLE_API_KEY=your_google_api_key_here
SUPABASE_DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
HUGGING_FACE_API_KEY=hf_your_token_here
REDIS_URL=redis://localhost:6379

# Voice Integration
VAPI_API_KEY=your_vapi_api_key_here
VAPI_WEBHOOK_SECRET=your_webhook_secret_here

# Vector Database (choose one)
USE_PINECONE=false  # Set to true for Pinecone
PINECONE_API_KEY=your_pinecone_key  # If using Pinecone
CHROMA_PERSIST_DIR=./data/vector_store  # If using ChromaDB
```

### Frontend Configuration (`nura-fe/.env.local`)

```bash
# Backend Connection
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase Authentication
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Voice Features
NEXT_PUBLIC_VAPI_PUBLIC_KEY=your_vapi_public_key
NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID=your_assistant_id
```

## 🧪 Testing & Development

### Health Checks

```bash
# Backend health check
curl http://localhost:8000/health

# Detailed system diagnostics
curl http://localhost:8000/health/detailed

# Service status checks
curl http://localhost:8000/health/services
```

### API Testing

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd nura-fe
npm test
```

## 📖 Documentation

Detailed documentation is available in the `/docs` folder:

- **[Frontend Guide](./docs/FRONTEND_COMPREHENSIVE_GUIDE.md)** - Complete frontend development guide
- **[API Reference](./docs/FRONTEND_API_QUICK_REFERENCE.md)** - Backend API integration details
- **[Backend README](./backend/README.md)** - Backend architecture and endpoints
- **[Voice Integration](./nura-fe/VAPI_INTEGRATION.md)** - Voice feature setup and usage

## 🔧 Common Issues & Troubleshooting

### Backend Issues

- **Redis Connection Error**: Ensure Redis is running (`redis-server`)
- **Database Connection Error**: Check Supabase credentials and network connectivity
- **API Key Issues**: Verify all API keys are correctly set in `.env` file

### Frontend Issues

- **API Connection Error**: Verify `NEXT_PUBLIC_API_URL` points to running backend
- **Auth Issues**: Check Supabase configuration and keys
- **Build Errors**: Ensure all dependencies are installed (`npm install`)

### Performance Optimization

- **Memory Usage**: Monitor vector database size and configure retention policies
- **API Rate Limits**: Implement caching and request throttling
- **Database Performance**: Index frequently queried fields

## 🤝 Contributing

We welcome contributions! Please read our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🔒 Privacy & Security

Nura takes privacy seriously:

- **Data Encryption**: All data is encrypted in transit and at rest
- **PII Detection**: Automatic detection and handling of personally identifiable information
- **User Control**: Users have full control over their data retention and deletion
- **GDPR Compliant**: Designed to meet GDPR and other privacy regulations
- **No Data Selling**: We never sell or share personal data with third parties

## 📞 Support & Resources

- **Crisis Resources**: Integrated crisis hotlines and emergency contacts
- **Documentation**: Comprehensive guides and API documentation
- **Community**: Join our community discussions
- **Issues**: Report bugs and request features on GitHub

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**⚠️ Important Disclaimer**: Nura is designed to complement, not replace, professional mental health care. If you're experiencing a mental health crisis, please contact emergency services or a mental health professional immediately.

**Crisis Resources:**

- **National Suicide Prevention Lifeline**: 988 (US)
- **Crisis Text Line**: Text HOME to 741741
- **Emergency Services**: 911 (US) / 999 (UK) / 112 (EU)

---

_Built with ❤️ for mental health awareness and support_
