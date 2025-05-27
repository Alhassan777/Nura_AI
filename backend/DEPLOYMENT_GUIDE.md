# Nura Backend Deployment Guide

## Overview

The Nura backend supports two deployment modes:

1. **Centralized Deployment** (Recommended) - All services in one application
2. **Standalone Deployment** - Each service runs independently

## 🚀 Centralized Deployment (Recommended)

Run all services together using the main application:

```bash
cd backend
python main.py
```

**Features:**

- Single application with all endpoints
- Unified API documentation at `/docs`
- Consistent CORS and middleware configuration
- Easier deployment and monitoring
- All endpoints available under `/api` prefix

**Available Endpoints:**

- `/api/health` - Health checks and configuration status
- `/api/memory` - Memory storage and retrieval
- `/api/chat` - Mental health assistant chat
- `/api/privacy` - Privacy review and consent management
- `/api/voice` - Voice call management and webhooks

**Port:** 8000 (default)

## 🔧 Standalone Deployment

Run services independently for development or microservices architecture:

### Memory Service Standalone

```bash
cd backend/services/memory
python memory_standalone.py
```

- **Port:** 8000
- **Endpoints:** Memory-specific endpoints only

### Voice Service Standalone

```bash
cd backend/services/voice
python voice_standalone.py
```

- **Port:** 8001
- **Endpoints:** Voice-specific endpoints only

## 📁 File Structure

```
backend/
├── main.py                           # 🎯 Centralized application
├── api/                              # 📦 Modular API components
│   ├── memory.py                     # Memory endpoints
│   ├── chat.py                       # Chat endpoints
│   ├── privacy.py                    # Privacy endpoints
│   └── health.py                     # Health endpoints
├── services/
│   ├── memory/
│   │   ├── memory_standalone.py      # 🔧 Standalone memory service
│   │   └── api.py                    # Legacy monolithic API (deprecated)
│   └── voice/
│       ├── voice_standalone.py       # 🔧 Standalone voice service
│       └── api.py                    # Voice API module
└── utils/                            # Shared utilities
```

## 🌐 Environment Configuration

Both deployment modes use the same environment variables:

```bash
# Required
GOOGLE_API_KEY=your_google_api_key

# Vector Database (choose one)
PINECONE_API_KEY=your_pinecone_key          # For Pinecone
GOOGLE_CLOUD_PROJECT=your_project_id        # For Vertex AI

# Optional
REDIS_URL=redis://localhost:6379
VAPI_API_KEY=your_vapi_key
```

## 🔍 Health Monitoring

### Centralized Mode

```bash
curl http://localhost:8000/api/health
```

### Standalone Mode

```bash
# Memory service
curl http://localhost:8000/health

# Voice service
curl http://localhost:8001/health
```

## 📊 API Documentation

### Centralized Mode

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Standalone Mode

- **Memory:** http://localhost:8000/docs
- **Voice:** http://localhost:8001/docs

## 🚦 Migration Path

If you're currently using standalone services:

1. **Stop standalone services**
2. **Start centralized service:** `python backend/main.py`
3. **Update frontend URLs** to use `/api` prefix
4. **Test all functionality** using `/api/health`

## 🛠️ Development Recommendations

- **Production:** Use centralized deployment
- **Development:** Use centralized deployment for simplicity
- **Microservices:** Use standalone deployment if needed
- **Testing:** Both modes support the same functionality

## 🔧 Troubleshooting

### Port Conflicts

If you get port conflicts:

- Centralized: Change `PORT` environment variable
- Standalone: Modify port in respective `*_standalone.py` files

### Import Errors

- Ensure you're running from the correct directory
- Check that all dependencies are installed
- Verify environment variables are set

### Configuration Issues

- Use `/api/health/config/test` to verify configuration
- Check logs for missing environment variables
- Refer to `.env.example` for required variables

## 📝 Notes

- The legacy `services/memory/api.py` is deprecated in favor of modular components
- Standalone files are maintained for flexibility but centralized deployment is recommended
- All services share the same utilities and configuration system
