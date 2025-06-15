# Voice Service Integration - Current Implementation

This document describes the Vapi.ai voice integration implemented in the Nura mental health application, providing voice-based interactions with the refactored mental health assistant.

## Architecture Overview

The voice service provides a clean, scalable architecture that integrates with the main Nura backend while leveraging Vapi's infrastructure for speech processing:

```
┌─────────────────────────┐    ┌──────────────────────────┐
│  Next.js Frontend       │◄──►│  Nura Backend API        │
│  • Supabase Auth        │    │  • JWT Authentication    │
│  • Vapi Web SDK         │    │  • Voice Service         │
└─────────┬───────────────┘    └──────────┬───────────────┘
          │                               │
 WebSocket│                      REST     │
 events   │                               ▼
┌─────────▼───────────────┐    ┌──────────────────────────┐
│  Voice Service API      │    │  Mental Health Assistant │
│  (backend/services/     │    │  (Refactored)            │
│   voice/)               │    │  • Crisis Detection      │
└─────────┬───────────────┘    │  • Memory Integration    │
          │                    │  • Parallel Processing   │
   HTTPS  │                    └──────────┬───────────────┘
          ▼                               │
   ┌─────────────┐                       ▼
   │ Vapi.ai API │◄─────────────┐ ┌────────────────────┐
   │ • Voice     │              │ │ Memory & Storage   │
   │   Calls     │              │ │ • Redis (short)    │
   │ • Webhooks  │              │ │ • Vector (long)    │
   └─────┬───────┘              │ └────────────────────┘
         │ call events          │
         ▼                      │
┌─────────────────────────┐     │
│  Supabase Database      │     │
│  • voices              │     │
│  • voice_calls         │     │
│  • call_summaries      │     │
│  • voice_schedules     │     │
│  • webhook_events      │     │
└─────────────────────────┘     │
```

## Key Features

### 1. Voice-Enabled Mental Health Assistant

- **Integration**: Connects voice input to the refactored mental health assistant
- **Crisis Detection**: Voice-based crisis assessment and intervention
- **Memory Integration**: Voice conversations contribute to user memory systems
- **Privacy Compliant**: No transcript storage, only processed summaries

### 2. User Authentication & Security

- **JWT Integration**: Secure user authentication via Supabase
- **User Isolation**: Voice data scoped to individual users
- **Privacy Protection**: Sensitive information handling compliant with mental health regulations
- **Audit Logging**: Comprehensive logging for compliance and debugging

### 3. Real-time Voice Processing

- **Vapi Integration**: Real-time speech-to-text and text-to-speech
- **Webhook Processing**: Real-time event handling for call lifecycle
- **Memory Processing**: Background memory extraction from conversations
- **Crisis Intervention**: Immediate crisis detection and response during calls

### 4. Flexible Call Management

- **Browser Calls**: Direct web-based voice interactions
- **Phone Calls**: Traditional phone number-based calling
- **Scheduled Calls**: Automated wellness check-ins and reminders
- **Call History**: Comprehensive call tracking and analytics

## Database Schema

### Core Tables

| Table             | Purpose                            | Key Fields                                     |
| ----------------- | ---------------------------------- | ---------------------------------------------- |
| `voices`          | Available voice assistants         | `assistant_id`, `name`, `sample_url`           |
| `voice_calls`     | Call metadata and status           | `vapi_call_id`, `user_id`, `channel`, `status` |
| `call_summaries`  | **Summaries only, NO transcripts** | `summary_json`, `sentiment`, `key_topics`      |
| `voice_schedules` | Recurring call schedules           | `cron_expression`, `next_run_at`, `user_id`    |
| `webhook_events`  | Vapi event logging                 | `event_type`, `payload`, `processed_at`        |

### Data Flow & Privacy

```sql
-- ✅ We DO store processed summaries
CREATE TABLE call_summaries (
  id VARCHAR PRIMARY KEY,
  call_id VARCHAR REFERENCES voice_calls(id),
  user_id VARCHAR NOT NULL,
  summary_json JSONB,        -- Processed summary from Vapi
  duration_seconds INTEGER,
  sentiment VARCHAR,         -- positive/negative/neutral
  key_topics JSONB,         -- Array of topics
  action_items JSONB,       -- Extracted action items
  crisis_indicators JSONB,  -- Crisis assessment results
  emotional_state VARCHAR,  -- Overall assessment
  created_at TIMESTAMP DEFAULT NOW()
);

-- ❌ We DON'T store raw transcripts
-- transcript_text NOT STORED for privacy
```

## API Endpoints

### Voice Management

| Endpoint                    | Method | Description               | Authentication |
| --------------------------- | ------ | ------------------------- | -------------- |
| `GET /voice/voices`         | GET    | List available voices     | Required       |
| `POST /voice/calls/browser` | POST   | Start browser call        | Required       |
| `POST /voice/calls/phone`   | POST   | Queue outbound phone call | Required       |
| `GET /voice/calls`          | GET    | List user's calls         | Required       |

### Scheduling

| Endpoint                       | Method | Description                    | Authentication |
| ------------------------------ | ------ | ------------------------------ | -------------- |
| `POST /voice/schedules`        | POST   | Create recurring call schedule | Required       |
| `GET /voice/schedules`         | GET    | List user's schedules          | Required       |
| `PUT /voice/schedules/{id}`    | PUT    | Update schedule                | Required       |
| `DELETE /voice/schedules/{id}` | DELETE | Delete schedule                | Required       |

### Analytics & History

| Endpoint                    | Method | Description          | Authentication |
| --------------------------- | ------ | -------------------- | -------------- |
| `GET /voice/summaries`      | GET    | List call summaries  | Required       |
| `GET /voice/summaries/{id}` | GET    | Get specific summary | Required       |

### System Integration

| Endpoint              | Method | Description           | Authentication |
| --------------------- | ------ | --------------------- | -------------- |
| `POST /voice/webhook` | POST   | Process Vapi webhooks | Internal       |
| `GET /voice/health`   | GET    | Service health check  | None           |

## Request/Response Examples

### 1. Start Browser Call

```typescript
// Frontend
const response = await fetch("/api/voice/calls/browser", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${userToken}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    assistant_id: "your-assistant-id",
  }),
});

const { success, vapi_call_id, assistant_id } = await response.json();

// Initialize Vapi Web SDK
vapi.start(assistant_id, {
  metadata: { user_id: currentUserId },
});
```

### 2. Schedule Recurring Call

```typescript
const response = await fetch("/api/voice/schedules", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${userToken}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    name: "Daily Check-in",
    assistant_id: "assistant-id",
    cron_expression: "0 9 * * *", // Daily at 9 AM
    timezone: "America/New_York",
    is_active: true,
  }),
});
```

### 3. Get Call Summary

```typescript
const response = await fetch(`/api/voice/summaries/${callId}`, {
  headers: {
    Authorization: `Bearer ${userToken}`,
  },
});

const summary = await response.json();
// Returns: summary_json, sentiment, key_topics, action_items, etc.
```

## Integration with Mental Health Assistant

### Memory Processing

Voice conversations are processed through the same refactored mental health assistant:

```python
# After voice call completion
async def process_voice_call_completion(call_data):
    user_id = call_data["metadata"]["user_id"]
    summary = call_data["analysis"]["summary"]

    # Process through refactored assistant for memory extraction
    assistant_response = await mental_health_assistant.process_voice_summary(
        user_id=user_id,
        voice_summary=summary,
        call_metadata=call_data
    )

    # Extract and store memories
    if assistant_response.get("memories_extracted"):
        await memory_service.store_memories(
            user_id=user_id,
            memories=assistant_response["memories"],
            source="voice_call"
        )
```

### Crisis Detection

Voice calls benefit from the same crisis detection capabilities:

```python
async def analyze_voice_crisis_indicators(call_summary):
    crisis_assessment = await mental_health_assistant.assess_crisis_level(
        content=call_summary,
        source="voice"
    )

    if crisis_assessment["level"] == "CRISIS":
        await safety_network_service.trigger_emergency_contacts(
            user_id=user_id,
            crisis_data=crisis_assessment,
            source="voice_call"
        )
```

## Environment Configuration

Add to your `backend/.env`:

```bash
# Vapi Configuration
VAPI_API_KEY=your_vapi_server_api_key
NEXT_PUBLIC_VAPI_PUBLIC_KEY=your_vapi_public_key
NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID=your_default_assistant_id
VAPI_ASSISTANT_ID=your_default_assistant_id
VAPI_BASE_URL=https://api.vapi.ai
VAPI_WEBHOOK_SECRET=your_webhook_secret

# Voice Service Database (uses main Supabase database)
VOICE_DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# Voice Service Settings
SCHEDULER_ENABLED=true
SCHEDULER_CHECK_INTERVAL_SECONDS=60
MAX_CALL_DURATION_MINUTES=30
MAX_CONCURRENT_CALLS_PER_USER=1
VOICE_QUEUE_MAX_RETRIES=3
```

## Frontend Integration

### Vapi Web SDK Setup

```typescript
// Install Vapi SDK
npm install @vapi-ai/web

// Initialize in component
import Vapi from "@vapi-ai/web";

const vapi = new Vapi(process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY);

// Start voice call
const startVoiceCall = async () => {
  const response = await fetch("/api/voice/calls/browser", {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}` }
  });

  const { assistant_id } = await response.json();

  vapi.start(assistant_id, {
    metadata: { user_id: currentUser.id }
  });
};
```

### Voice Call Status Monitoring

```typescript
vapi.on("call-start", () => {
  console.log("Voice call started");
});

vapi.on("call-end", () => {
  console.log("Voice call ended");
  // Refresh call history or summaries
});

vapi.on("error", (error) => {
  console.error("Voice call error:", error);
});
```

## Performance & Scalability

### Response Times

- **Call Initiation**: <2 seconds to start voice call
- **Crisis Detection**: Real-time during conversation
- **Memory Processing**: Background, does not block call
- **Summary Generation**: <5 seconds post-call

### Scalability Features

- **Concurrent Calls**: Configurable limits per user
- **Queue Management**: Background job processing for phone calls
- **Error Recovery**: Automatic retry logic with exponential backoff
- **Load Balancing**: Stateless design supports horizontal scaling

## Security & Privacy

### Data Protection

- **No Transcript Storage**: Only processed summaries stored
- **User Isolation**: All data scoped to authenticated users
- **Webhook Verification**: HMAC verification for Vapi webhooks
- **Audit Logging**: Complete audit trail for all voice interactions

### Compliance

- **HIPAA Ready**: Designed for healthcare data compliance
- **GDPR Compliant**: User control over data retention and deletion
- **Mental Health Standards**: Follows best practices for sensitive mental health data

This voice service integration provides a secure, scalable foundation for voice-based mental health support while maintaining the same high standards of privacy and security as the rest of the Nura platform.
