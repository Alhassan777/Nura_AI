# Nura Backend

Mental health chat application backend with modular architecture and voice integration.

## 🏗️ Architecture

The Nura backend features a **modular architecture** that supports both centralized and standalone deployment:

```
backend/
├── main.py                    # 🎯 Centralized FastAPI application
├── api/                       # 📦 Modular API components
│   ├── memory.py             # Memory storage & retrieval
│   ├── chat.py               # Mental health assistant
│   ├── privacy.py            # Privacy & consent management
│   └── health.py             # Health checks & monitoring
├── services/                  # 🔧 Business logic services
│   ├── memory/               # Memory processing service
│   ├── voice/                # Voice call management
│   └── chat/                 # Chat processing
└── utils/                    # 🛠️ Shared utilities
```

## 🚀 Quick Start

### Centralized Deployment (Recommended)

```bash
cd backend
python main.py
```

Access the API at: http://localhost:8000/docs

### Standalone Services

```bash
# Memory service only
cd backend/services/memory
python memory_standalone.py

# Voice service only
cd backend/services/voice
python voice_standalone.py
```

## 📋 Features

### 🧠 Memory Management

- **Dual Storage Strategy**: Short-term (Redis) + Long-term (Vector DB)
- **PII Detection**: Automatic sensitive data identification
- **Privacy Controls**: Granular consent management
- **Emotional Anchors**: Meaningful connection tracking

### 💬 Mental Health Assistant

- **Crisis Detection**: Automatic risk assessment
- **Memory Integration**: Personalized responses
- **Resource Provision**: Crisis hotlines and coping strategies
- **Therapeutic Continuity**: Cross-session context

### 🎙️ Voice Integration

- **Vapi.ai Integration**: Voice call management
- **Call Mapping**: Customer ID to call ID mapping
- **Webhook Processing**: Real-time conversation updates
- **Metrics Tracking**: Latency and performance monitoring

### 🔒 Privacy & Security

- **PII Anonymization**: Configurable data protection
- **Consent Management**: User control over data storage
- **Audit Trail**: Complete privacy decision tracking
- **HIPAA Considerations**: Healthcare-grade privacy controls

## 🌐 API Endpoints

### Health & Configuration

- `GET /api/health` - Service health check
- `GET /api/health/config/test` - Configuration validation
- `GET /api/health/services` - Service status monitoring

### Memory Management

- `POST /api/memory/` - Process and store memory
- `GET /api/memory/context` - Retrieve memory context
- `GET /api/memory/stats` - Memory statistics
- `POST /api/memory/dual-storage` - Dual storage processing

### Chat Assistant

- `POST /api/chat/assistant` - Chat with mental health assistant
- `GET /api/chat/crisis-resources` - Get crisis resources

### Privacy Controls

- `GET /api/privacy/review/{user_id}` - Review memories with PII
- `POST /api/privacy/apply-choices/{user_id}` - Apply privacy choices

### Voice Management

- `POST /api/voice/mapping` - Store call mappings
- `POST /api/voice/process-event` - Process voice events
- `GET /api/voice/metrics/latency` - Voice metrics

## ⚙️ Configuration

### Required Environment Variables

```bash
GOOGLE_API_KEY=your_google_api_key
```

### Vector Database (Choose One)

```bash
# Option 1: Pinecone
PINECONE_API_KEY=your_pinecone_key

# Option 2: Vertex AI
GOOGLE_CLOUD_PROJECT=your_project_id
```

### Optional Configuration

```bash
REDIS_URL=redis://localhost:6379
VAPI_API_KEY=your_vapi_key
HOST=0.0.0.0
PORT=8000
```

## 🔍 Monitoring

### Health Checks

```bash
# Overall health
curl http://localhost:8000/api/health

# Configuration test
curl http://localhost:8000/api/health/config/test

# Service status
curl http://localhost:8000/api/health/services
```

### Logs

- Application logs: `backend.log`
- Service-specific logs in respective service directories

## 🛠️ Development

### Project Structure

- **`api/`** - Modular API endpoints (new architecture)
- **`services/`** - Business logic and data processing
- **`utils/`** - Shared utilities and helpers
- **`*_standalone.py`** - Standalone service runners

### Adding New Endpoints

1. Create new module in `api/` directory
2. Define FastAPI router with endpoints
3. Include router in `main.py`
4. Update documentation

### Testing

```bash
# Run health check
curl http://localhost:8000/api/health

# Test configuration
curl http://localhost:8000/api/health/config/test

# View API docs
open http://localhost:8000/docs
```

## 📚 Documentation

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **Deployment Guide**: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

## 🔄 Migration from Legacy

If migrating from the old monolithic API:

1. **Stop old services**
2. **Start centralized service**: `python main.py`
3. **Update frontend URLs** to include `/api` prefix
4. **Test functionality** using health endpoints

## 🤝 Contributing

1. Follow the modular architecture pattern
2. Add new endpoints to appropriate `api/` modules
3. Keep business logic in `services/` directories
4. Update documentation and health checks
5. Test both centralized and standalone modes

## 📄 License

[Your License Here]
