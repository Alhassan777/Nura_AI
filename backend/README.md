# Nura Backend API Documentation

A comprehensive mental health support platform backend with modular microservices architecture.

## 🏗️ Architecture Overview

The Nura backend follows a **clean modular architecture** where each service is self-contained with its own API endpoints, business logic, and data models. All services can operate independently while communicating through well-defined interfaces.

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Main API      │    │   Services      │
│   (React/Next)  │◄──►│   (FastAPI)     │◄──►│   (Modular)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Database      │    │   External APIs │
                    │   (Supabase)    │    │   (OpenAI, etc) │
                    └─────────────────┘    └─────────────────┘
```

## 📁 Directory Structure

```
backend/
├── main.py                     # 🚀 Main FastAPI application
├── README.md                   # 📖 This documentation
├── requirements.txt            # 📦 Python dependencies
├── .env.example               # 🔧 Environment variables template
├── backend.log                # 📝 Application logs
│
├── api/                       # 🌐 Standalone API modules
│   └── health.py             # ❤️ Health monitoring & diagnostics
│
├── services/                  # 🔧 Modular service architecture
│   ├── memory/               # 🧠 Memory & context management
│   │   ├── api.py           # API endpoints
│   │   ├── memoryService.py # Core business logic
│   │   ├── config.py        # Configuration
│   │   ├── types.py         # Data models
│   │   └── storage/         # Storage implementations
│   │
│   ├── chat/                # 💬 Conversational interface
│   │   ├── api.py          # Chat endpoints
│   │   ├── database.py     # Database models
│   │   └── user_integration.py
│   │
│   ├── voice/               # 🎤 Voice interaction service
│   │   ├── api.py          # Voice endpoints
│   │   ├── vapi_client.py  # External voice API client
│   │   └── config.py       # Voice configuration
│   │
│   ├── image_generation/    # 🎨 Emotional visualization
│   │   ├── api.py          # Image generation endpoints
│   │   ├── emotion_visualizer.py
│   │   ├── image_generator.py
│   │   └── prompt_builder.py
│   │
│   ├── assistant/           # 🤖 AI mental health assistant
│   │   ├── api.py          # Assistant endpoints
│   │   └── mental_health_assistant.py
│   │
│   ├── privacy/             # 🔒 PII detection & privacy
│   │   ├── api.py          # Privacy endpoints
│   │   └── processors/     # Privacy processing logic
│   │
│   ├── user/                # 👤 User management
│   │   ├── api.py          # User CRUD endpoints
│   │   └── auth_endpoints.py # Authentication
│   │
│   ├── scheduling/          # 📅 Appointment & reminder system
│   │   └── api.py          # Scheduling endpoints
│   │
│   ├── audit/               # 📊 Compliance & logging
│   │   └── api.py          # Audit endpoints
│   │
│   └── safety_network/      # 🚨 Crisis intervention
│       └── api.py          # Safety network endpoints
│
├── utils/                   # 🛠️ Shared utilities
│   ├── auth.py             # JWT authentication system
│   ├── redis_client.py     # Redis connection utilities
│   ├── voice.py            # Voice processing utilities
│   └── prompts/            # AI prompt templates
│       ├── chat/           # Chat-specific prompts
│       └── voice/          # Voice-specific prompts
│
└── models/                  # 📋 Shared data models
    └── (database models)
```

## 🔐 Authentication System

**JWT-based authentication** secures all user-specific endpoints. Users can only access their own data.

### Authentication Flow

```
1. User logs in → Receives JWT token
2. Frontend stores token → Sends in Authorization header
3. Backend validates token → Extracts user_id
4. All operations scoped to authenticated user
```

### Headers Required

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

## 🌐 API Endpoints Reference

Base URL: `http://localhost:8000` (development)

### 🏠 Core Endpoints

| Endpoint              | Method | Description                   | Auth Required |
| --------------------- | ------ | ----------------------------- | ------------- |
| `/`                   | GET    | API information               | ❌            |
| `/docs`               | GET    | Interactive API documentation | ❌            |
| `/health`             | GET    | Main health check             | ❌            |
| `/health/config/test` | GET    | Configuration validation      | ❌            |
| `/health/services`    | GET    | Service status checks         | ❌            |
| `/health/detailed`    | GET    | Comprehensive diagnostics     | ❌            |

### 🧠 Memory Service (`/memory`)

**Purpose**: Stores and retrieves user memories, provides context for conversations.

| Endpoint                    | Method | Description                    | Auth Required |
| --------------------------- | ------ | ------------------------------ | ------------- |
| `/memory/store`             | POST   | Store new memory               | ✅            |
| `/memory/search`            | GET    | Search user memories           | ✅            |
| `/memory/push`              | POST   | Push memory (Vapi integration) | ❌            |
| `/memory/context/{user_id}` | GET    | Get memory context             | ✅            |
| `/memory/stats/{user_id}`   | GET    | Memory statistics              | ✅            |
| `/memory/consent`           | POST   | Handle memory consent          | ✅            |

**Example Request:**

```json
POST /memory/store
{
  "content": "I had a great day at the park",
  "type": "reflection",
  "metadata": {
    "mood": "positive",
    "location": "park"
  }
}
```

### 💬 Chat Service (`/chat`)

**Purpose**: Conversational interface with mental health assistant integration.

| Endpoint                            | Method | Description                  | Auth Required |
| ----------------------------------- | ------ | ---------------------------- | ------------- |
| `/chat/conversations`               | GET    | List user conversations      | ✅            |
| `/chat/conversations`               | POST   | Create new conversation      | ✅            |
| `/chat/messages`                    | POST   | Send message in conversation | ✅            |
| `/chat/conversations/{id}/messages` | GET    | Get conversation messages    | ✅            |
| `/chat/crisis-resources`            | GET    | Get crisis resources         | ❌            |
| `/chat/report-crisis`               | POST   | Report crisis situation      | ✅            |

**Example Flow:**

```json
1. POST /chat/conversations
   { "title": "Evening Reflection", "session_type": "chat" }

2. POST /chat/messages
   {
     "conversation_id": "conv_123",
     "content": "I've been feeling anxious lately"
   }

3. Response includes assistant reply + crisis assessment
```

### 🎤 Voice Service (`/voice`)

**Purpose**: Voice-based interactions through Vapi integration.

| Endpoint               | Method | Description           | Auth Required |
| ---------------------- | ------ | --------------------- | ------------- |
| `/voice/voices`        | GET    | List available voices | ❌            |
| `/voice/calls/browser` | POST   | Start browser call    | ✅            |
| `/voice/calls/phone`   | POST   | Start phone call      | ✅            |
| `/voice/calls`         | GET    | List user calls       | ✅            |
| `/voice/schedules`     | GET    | List voice schedules  | ✅            |
| `/voice/schedules`     | POST   | Create voice schedule | ✅            |
| `/voice/summaries`     | GET    | List call summaries   | ✅            |

**Browser Call Example:**

```json
POST /voice/calls/browser
{
  "assistant_id": "asst_123",
  "metadata": {
    "session_type": "therapy_check_in"
  }
}
```

### 🎨 Image Generation (`/image-generation`)

**Purpose**: Convert emotions and thoughts into visual representations.

| Endpoint                             | Method | Description                   | Auth Required |
| ------------------------------------ | ------ | ----------------------------- | ------------- |
| `/image-generation/generate`         | POST   | Generate emotional image      | ❌            |
| `/image-generation/validate`         | POST   | Validate input for generation | ❌            |
| `/image-generation/status/{user_id}` | GET    | Get generation status         | ❌            |
| `/image-generation/quick-generate`   | POST   | Quick generation (testing)    | ❌            |

**Example:**

```json
POST /image-generation/generate
{
  "user_id": "user_123",
  "user_input": "I feel like I'm floating in a calm blue ocean",
  "include_long_term_memory": true
}
```

### 🤖 Assistant Service (`/assistant`)

**Purpose**: AI-powered mental health support and crisis detection.

| Endpoint                       | Method | Description            | Auth Required |
| ------------------------------ | ------ | ---------------------- | ------------- |
| `/assistant/chat`              | POST   | Get assistant response | ❌            |
| `/assistant/crisis-assessment` | POST   | Assess crisis level    | ❌            |
| `/assistant/crisis-resources`  | GET    | Get crisis resources   | ❌            |

### 👤 User Management (`/users`, `/auth`)

**Purpose**: User accounts, authentication, and profile management.

| Endpoint        | Method | Description              | Auth Required |
| --------------- | ------ | ------------------------ | ------------- |
| `/auth/signup`  | POST   | Create new account       | ❌            |
| `/auth/login`   | POST   | User login               | ❌            |
| `/auth/logout`  | POST   | User logout              | ✅            |
| `/auth/refresh` | POST   | Refresh JWT token        | ✅            |
| `/users/me`     | GET    | Get current user profile | ✅            |
| `/users/me`     | PUT    | Update user profile      | ✅            |

### 🔒 Privacy Service (`/privacy`)

**Purpose**: PII detection, anonymization, and privacy compliance.

| Endpoint             | Method | Description              | Auth Required |
| -------------------- | ------ | ------------------------ | ------------- |
| `/privacy/analyze`   | POST   | Analyze text for PII     | ❌            |
| `/privacy/anonymize` | POST   | Anonymize sensitive data | ❌            |
| `/privacy/settings`  | GET    | Get privacy settings     | ✅            |

### 📅 Scheduling Service (`/scheduling`)

**Purpose**: Appointment scheduling and reminder management.

| Endpoint                     | Method | Description         | Auth Required |
| ---------------------------- | ------ | ------------------- | ------------- |
| `/scheduling/schedules`      | GET    | List user schedules | ✅            |
| `/scheduling/schedules`      | POST   | Create new schedule | ✅            |
| `/scheduling/schedules/{id}` | PUT    | Update schedule     | ✅            |
| `/scheduling/schedules/{id}` | DELETE | Delete schedule     | ✅            |

### 📊 Audit Service (`/audit`)

**Purpose**: Compliance logging and audit trail management.

| Endpoint      | Method | Description      | Auth Required |
| ------------- | ------ | ---------------- | ------------- |
| `/audit/log`  | POST   | Log audit event  | ❌            |
| `/audit/logs` | GET    | Query audit logs | ❌            |

### 🚨 Safety Network (`/safety_network`)

**Purpose**: Crisis intervention and emergency contact management.

| Endpoint                   | Method | Description             | Auth Required |
| -------------------------- | ------ | ----------------------- | ------------- |
| `/safety_network/contacts` | GET    | List emergency contacts | ✅            |
| `/safety_network/contacts` | POST   | Add emergency contact   | ✅            |
| `/safety_network/alert`    | POST   | Send crisis alert       | ✅            |

## 🔄 System Flow Diagrams

### User Registration & Authentication Flow

```
Frontend → POST /auth/signup → Backend
                ↓
         Validates & creates user
                ↓
         Returns JWT token
                ↓
Frontend stores token → All subsequent requests use token
```

### Conversation Flow

```
Frontend → POST /chat/conversations → Create conversation
    ↓
Frontend → POST /chat/messages → Send user message
    ↓
Backend → Memory Service → Store/retrieve context
    ↓
Backend → Assistant Service → Generate response
    ↓
Backend → Crisis Assessment → Check for crisis indicators
    ↓
Frontend ← Returns assistant response + metadata
```

### Voice Interaction Flow

```
Frontend → POST /voice/calls/browser → Get call config
    ↓
Frontend → Vapi SDK → Start voice call
    ↓
Vapi → Webhook → /vapi/webhooks → Backend processing
    ↓
Backend → Memory Service → Store conversation context
    ↓
Backend → Assistant Service → Generate responses
```

### Memory System Flow

```
Any Service → POST /memory/store → Store memory
    ↓
Memory Service → Vector DB → Store embeddings
    ↓
Memory Service → Redis → Cache recent context
    ↓
Later: GET /memory/context → Retrieve relevant memories
```

## 🚀 Getting Started for Frontend Developers

### 1. Environment Setup

```bash
# Backend setup
cd backend
pip install -r requirements.txt
cp .env.example .env
# Configure environment variables
python main.py
```

### 2. Test Backend Connection

```javascript
// Test health endpoint
fetch("http://localhost:8000/health")
  .then((res) => res.json())
  .then((data) => console.log("Backend status:", data));
```

### 3. Authentication Integration

```javascript
// Login
const loginResponse = await fetch("/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password",
  }),
});

const { token } = await loginResponse.json();
localStorage.setItem("jwt_token", token);

// Use token in subsequent requests
const headers = {
  Authorization: `Bearer ${localStorage.getItem("jwt_token")}`,
  "Content-Type": "application/json",
};
```

### 4. Chat Integration Example

```javascript
// Start a conversation
const conversation = await fetch("/chat/conversations", {
  method: "POST",
  headers,
  body: JSON.stringify({
    title: "Daily Check-in",
    session_type: "chat",
  }),
}).then((res) => res.json());

// Send a message
const messageResponse = await fetch("/chat/messages", {
  method: "POST",
  headers,
  body: JSON.stringify({
    conversation_id: conversation.id,
    content: "How can I manage my anxiety better?",
  }),
}).then((res) => res.json());

console.log("Assistant response:", messageResponse.assistant_response.content);
```

### 5. Voice Integration Example

```javascript
// Start browser call
const callConfig = await fetch("/voice/calls/browser", {
  method: "POST",
  headers,
  body: JSON.stringify({
    assistant_id: "asst_therapy_01",
    metadata: { session_type: "check_in" },
  }),
}).then((res) => res.json());

// Use with Vapi SDK
const vapi = new Vapi(callConfig.publicKey);
vapi.start(callConfig.assistantId, {
  metadata: callConfig.metadata,
});
```

## 🔧 Environment Variables

Create `.env` file with these variables:

```bash
# Core Configuration
HOST=0.0.0.0
PORT=8000
ENV=development

# Database
DATABASE_URL=postgresql://user:pass@localhost/nura
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key

# AI Services
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_key
HF_TOKEN=your_huggingface_token

# Voice Service
VAPI_API_KEY=your_vapi_private_key
VAPI_PUBLIC_KEY=your_vapi_public_key

# Vector Database
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_pinecone_env

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
```

## 📊 Error Handling

All endpoints return consistent error format:

```json
{
  "detail": "Error description",
  "status_code": 400,
  "error_type": "validation_error"
}
```

### Common HTTP Status Codes

- **200**: Success
- **400**: Bad request (validation error)
- **401**: Unauthorized (invalid/missing JWT)
- **403**: Forbidden (insufficient permissions)
- **404**: Not found
- **500**: Internal server error

## 🔍 Monitoring & Debugging

### Health Checks

- **`/health`**: Basic health status
- **`/health/services`**: Individual service status
- **`/health/detailed`**: Comprehensive diagnostics

### Logging

- Application logs: `backend.log`
- All requests are logged with user context
- Error stack traces included in development

### API Documentation

- Interactive docs: `http://localhost:8000/docs`
- OpenAPI spec: `http://localhost:8000/openapi.json`

## 🔒 Security Considerations

### For Frontend Developers

1. **Always use HTTPS** in production
2. **Store JWT tokens securely** (httpOnly cookies preferred)
3. **Validate user input** before sending to API
4. **Handle token expiration** gracefully
5. **Don't log sensitive data** (tokens, PII)
6. **Implement proper error boundaries**

### JWT Token Management

```javascript
// Check if token is expired
function isTokenExpired(token) {
  const payload = JSON.parse(atob(token.split(".")[1]));
  return Date.now() >= payload.exp * 1000;
}

// Auto-refresh token
async function refreshTokenIfNeeded() {
  const token = localStorage.getItem("jwt_token");
  if (token && isTokenExpired(token)) {
    const newToken = await fetch("/auth/refresh", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    }).then((res) => res.json());
    localStorage.setItem("jwt_token", newToken.token);
  }
}
```

## 🚀 Performance Tips

### For Frontend Integration

1. **Cache user data** appropriately
2. **Implement pagination** for lists (conversations, messages)
3. **Use WebSockets** for real-time features (chat)
4. **Debounce search requests**
5. **Lazy load** non-critical data
6. **Implement optimistic updates** for better UX

### Recommended Request Patterns

```javascript
// Debounced search
const debouncedSearch = useMemo(
  () =>
    debounce(async (query) => {
      const results = await fetch(`/memory/search?q=${query}`, { headers });
      return results.json();
    }, 300),
  [headers]
);

// Pagination
const getConversations = async (page = 1, limit = 20) => {
  const offset = (page - 1) * limit;
  return fetch(`/chat/conversations?limit=${limit}&offset=${offset}`, {
    headers,
  });
};
```

## 🤝 Contributing

### Adding New Endpoints

1. Create endpoint in appropriate service's `api.py`
2. Add authentication if needed: `user_id: str = Depends(get_current_user_id)`
3. Add request/response models with Pydantic
4. Update this README with endpoint documentation
5. Test endpoint in `/docs`

### Service Communication

Services communicate through:

- **Direct imports** for tight coupling
- **HTTP calls** for loose coupling
- **Shared utilities** in `utils/`

## 📞 Support

- **API Documentation**: `/docs`
- **Health Monitoring**: `/health/detailed`
- **Logs**: Check `backend.log`
- **Environment**: Verify `.env` configuration

---

## 🎯 Quick Reference for Frontend Developers

### Most Common Endpoints

```javascript
// Authentication
POST / auth / login; // Get JWT token
GET / users / me; // Get user profile

// Chat
POST / chat / conversations; // Start conversation
POST / chat / messages; // Send message
GET / chat / conversations; // List conversations

// Memory
POST / memory / store; // Store memory
GET / memory / search; // Search memories

// Voice
POST / voice / calls / browser; // Start voice call

// Health
GET / health; // Check backend status
```

### Essential Headers

```javascript
const headers = {
  Authorization: `Bearer ${jwt_token}`,
  "Content-Type": "application/json",
};
```

This backend provides a robust, scalable foundation for building comprehensive mental health applications! 🚀
