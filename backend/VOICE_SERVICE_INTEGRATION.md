# Voice Service Integration - Blueprint Architecture

This document describes the new Vapi.ai voice integration that implements the **component-level blueprint architecture** for the Nura mental health application.

## Architecture Overview

The voice service follows a clean, scalable architecture that keeps the backend lean while leveraging Vapi's infrastructure for all real-time speech processing:

```
┌─────────────────────────┐    ┌──────────────────────────┐
│  Next.js Frontend       │◄──►│  Memory Service API      │
│  • Auth / JWT          │    │  • REST endpoints        │
│  • Vapi Web SDK        │    │  • AuthZ middleware      │
└─────────┬───────────────┘    └──────────┬───────────────┘
          │                               │
 WebSocket│                      REST     │
 events   │                               ▼
┌─────────▼───────────────┐    ┌──────────────────────────┐
│  Webhook Handler        │    │  Job Queue (Redis)       │
│  (Frontend API)         │    │  • BullMQ-style          │
└─────────┬───────────────┘    │  • Cron scheduling       │
          │                    │  • Retry logic           │
   HTTPS  │                    └──────────┬───────────────┘
          ▼                               │
   ┌─────────────┐                       ▼
   │ Vapi Webhook│◄─────────────┐ ┌────────────────────┐
   │ /voice/     │              │ │ Vapi REST API      │
   │ webhook     │              │ │ • create call      │
   └─────┬───────┘              │ │ • get call         │
         │ analysis-complete    │ │ (metadata isolated)│
         ▼                      │ └────────────────────┘
┌─────────────────────────┐     │
│  PostgreSQL             │     │
│  • voices              │     │
│  • voice_calls         │     │
│  • call_summaries      │     │
│  • voice_schedules     │     │
│  (NO transcripts)      │     │
└─────────────────────────┘     │
```

## Key Features

### 1. Zero Transcript Storage

- **All speech processing stays in Vapi** - we never store raw transcripts
- Only processed summaries, sentiment analysis, and structured data are stored
- Dramatically reduces privacy concerns and storage costs
- Full compliance with mental health data regulations

### 2. Per-User Data Isolation

- Every call includes `metadata.userId` for strict user isolation
- Database queries are automatically filtered by user ID
- No cross-user data leakage possible
- Row-level security at the database level

### 3. Scalable Scheduling

- Redis-based job queue with BullMQ-style processing
- Cron expression support for complex recurring schedules
- Exponential backoff retry logic
- Horizontal scaling ready

### 4. Real-time Event Processing

- HMAC-verified webhooks from Vapi
- Event filtering (only process relevant events)
- Automatic user/call mapping via metadata
- WebSocket support for frontend updates

## Database Schema

### Core Tables

| Table             | Purpose                            | Key Fields                                     |
| ----------------- | ---------------------------------- | ---------------------------------------------- |
| `voices`          | Available voice assistants         | `assistant_id`, `name`, `sample_url`           |
| `voice_calls`     | Call metadata and status           | `vapi_call_id`, `user_id`, `channel`, `status` |
| `call_summaries`  | **Summaries only, NO transcripts** | `summary_json`, `sentiment`, `key_topics`      |
| `voice_schedules` | Recurring call schedules           | `cron_expression`, `next_run_at`, `user_id`    |
| `voice_users`     | User profiles for voice service    | `phone`, `email`, `id`                         |

### No Transcript Storage

```sql
-- ❌ We DON'T store this
CREATE TABLE transcripts (
  content TEXT -- NEVER STORED
);

-- ✅ We DO store this
CREATE TABLE call_summaries (
  summary_json JSONB,     -- Processed summary from Vapi
  sentiment VARCHAR,      -- positive/negative/neutral
  key_topics JSONB,      -- Array of topics
  emotional_state VARCHAR -- Overall assessment
);
```

## API Endpoints

### Voice Management

- `GET /voice/voices` - List available voices
- `POST /voice/calls/browser` - Start browser call (Web SDK config)
- `POST /voice/calls/phone` - Queue outbound phone call
- `GET /voice/calls` - List user's calls (filtered by user)

### Scheduling

- `POST /voice/schedules` - Create recurring call schedule
- `GET /voice/schedules` - List user's schedules
- `PUT /voice/schedules/{id}` - Update schedule
- `DELETE /voice/schedules/{id}` - Delete schedule

### Analytics (Summary Only)

- `GET /voice/summaries` - List call summaries (no transcripts)
- `GET /voice/summaries/{id}` - Get specific summary

### Webhooks (Internal)

- `POST /voice/webhook` - Process Vapi webhooks
- `GET /voice/health` - Service health check

## Request/Response Flow

### 1. Browser Call (Inbound)

```typescript
// Frontend
const response = await fetch("/api/voice/start", {
  method: "POST",
  body: JSON.stringify({
    mode: "web",
    assistantId: "assistant-id",
    metadata: { sessionId: "abc123" },
  }),
});

const { config } = await response.json();
vapi.start(config.assistantId, {
  metadata: config.metadata,
});
```

### 2. Phone Call (Outbound)

```typescript
// Frontend triggers
const response = await fetch("/api/voice/start", {
  method: "POST",
  body: JSON.stringify({
    mode: "phone",
    phoneNumber: "+1234567890",
    assistantId: "assistant-id",
  }),
});

// Backend queues job
await voice_queue.enqueue_call(user_id, assistant_id, phone_number);
```

### 3. Webhook Processing

```python
# Vapi sends webhook
{
  "type": "analysis-complete",
  "call": { "id": "call-123", "metadata": {"userId": "user-456"} },
  "analysis": {
    "sentiment": "positive",
    "summary": "User discussed coping strategies...",
    "keyTopics": ["anxiety", "work-stress"],
    # NO TRANSCRIPT INCLUDED
  }
}

# We store summary only
summary = CallSummary(
  call_id=call_record.id,
  user_id=user_id,
  summary_json=analysis_data,  # Structured summary
  sentiment=analysis_data.get("sentiment"),
  # transcript=None  # NEVER STORED
)
```

## Environment Configuration

Add to your `backend/.env`:

```bash
# Voice Service Database (separate from memory service)
VOICE_DATABASE_URL=postgresql://localhost:5432/nura_voice

# Vapi Configuration
VAPI_API_KEY=your_api_key
VAPI_PUBLIC_KEY=your_public_key
VAPI_DEFAULT_ASSISTANT_ID=your_assistant_id
VAPI_WEBHOOK_SECRET=your_webhook_secret

# Scheduling
SCHEDULER_ENABLED=true
SCHEDULER_CHECK_INTERVAL_SECONDS=60

# Call Limits
MAX_CALL_DURATION_MINUTES=30
MAX_CONCURRENT_CALLS_PER_USER=1

# Backend Integration
BACKEND_VOICE_URL=http://localhost:8000
```

## Getting Started

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
cd backend
python -c "from services.voice.init_db import init_voice_database; import asyncio; asyncio.run(init_voice_database())"
```

### 3. Start Services

```bash
cd backend
python start_services.py
```

This starts both Memory and Voice services on port 8000:

- Memory Service: `http://localhost:8000`
- Voice Service: `http://localhost:8000/voice`
- API Docs: `http://localhost:8000/docs`

### 4. Test the Integration

```bash
# Test voice service health
curl http://localhost:8000/voice/health

# List available voices
curl http://localhost:8000/voice/voices

# Create a phone call (requires valid phone number and assistant)
curl -X POST http://localhost:8000/voice/calls/phone \
  -H "Content-Type: application/json" \
  -H "X-User-ID: demo-user-123" \
  -d '{"assistant_id": "your-assistant-id", "phone_number": "+1234567890"}'
```

## Cost & Performance Benefits

| Aspect                   | Traditional Architecture      | Blueprint Architecture         |
| ------------------------ | ----------------------------- | ------------------------------ |
| **Transcript Storage**   | Full transcripts + processing | Zero storage, Vapi processes   |
| **Real-time Processing** | Custom STT/TTS/LLM pipeline   | Vapi handles all < 500ms       |
| **Data Privacy**         | Complex PII scrubbing         | No transcripts = no PII risk   |
| **Scaling**              | Heavy compute infrastructure  | Lightweight metadata only      |
| **Cost**                 | STT+LLM+TTS+Storage+Compute   | $0.05/min + wholesale AI costs |

## Security Features

- **HMAC Webhook Verification** - All webhooks cryptographically verified
- **User Isolation** - Automatic filtering by `metadata.userId`
- **No Transcript Storage** - Zero sensitive audio content stored
- **Row-Level Security** - Database queries scoped to authenticated user
- **Audit Logging** - All webhook events logged for debugging

This architecture keeps your backend lean while providing enterprise-grade voice capabilities through Vapi's infrastructure.
