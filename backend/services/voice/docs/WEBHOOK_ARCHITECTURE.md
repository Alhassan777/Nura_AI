# Webhook Architecture - Vapi through Supabase

## Overview

This document describes the consolidated webhook architecture where **Vapi webhooks flow through Supabase Edge Functions** and then to a **dedicated Vapi webhook endpoint** in our backend.

## Architecture Flow

```
Vapi → Supabase Edge Function → Backend /vapi/webhooks → Tool Logic
```

### Previous Architecture (DEPRECATED)

```
❌ Vapi → /vapi/webhooks → webhook_handler.py (direct, multiple handlers)
❌ Vapi → /voice/webhooks → api.py (duplicate endpoint)
❌ Multiple webhook files with duplicated logic
```

### New Unified Architecture ✅

```
✅ Vapi → Supabase Edge Function → /vapi/webhooks → vapi_webhook_router.py
✅ Single consolidated webhook processor
✅ All voice tools routed through one handler
```

## Benefits

1. **Centralized Management**: All Vapi webhooks go through Supabase for consistent handling
2. **Security**: Supabase handles authentication and validation
3. **Logging**: Centralized logging through Supabase
4. **Scalability**: Supabase Edge Functions can handle scaling
5. **Simplicity**: Single endpoint for all Vapi webhook types

## Implementation Details

### Main Webhook Endpoint

**Location**: `backend/main.py`
**Endpoint**: `POST /vapi/webhooks`

This endpoint:

- Receives ALL Vapi webhook calls from Supabase Edge Functions
- Routes all calls to the unified vapi_webhook_router
- Handles errors gracefully to prevent retries
- Supports both GET (health check) and POST (webhooks)

#### Routing Logic

```python
# All webhooks on /vapi/webhooks go to the voice service
from services.voice.vapi_webhook_router import vapi_webhook_router
result = await vapi_webhook_router.process_webhook(payload, headers)
return result
```

### Voice Webhook Processing

**Location**: `backend/services/voice/vapi_webhook_router.py`

Handles ALL Vapi-related webhooks:

- Crisis intervention tools
- General voice tools (pause, end call, status check)
- Scheduling tools
- Safety checkup tools
- Image generation tools
- Memory tools
- Call event processing (start, end, analysis)

### Webhook Endpoint

| Endpoint         | Handler                                 | Purpose                              |
| ---------------- | --------------------------------------- | ------------------------------------ |
| `/vapi/webhooks` | `vapi_webhook_router.process_webhook()` | All Vapi voice tool calls and events |

## Supabase Edge Function Setup

Supabase Edge Functions should:

1. **Receive webhooks** from Vapi
2. **Forward to** `https://your-backend.com/vapi/webhooks`
3. **Optional**: Add additional headers or validation

### Example Edge Function

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

serve(async (req) => {
  try {
    const payload = await req.json();

    // Forward directly to backend vapi webhook endpoint
    const response = await fetch("https://your-backend.com/vapi/webhooks", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-forwarded-from": "supabase",
      },
      body: JSON.stringify(payload),
    });

    return response;
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
});
```

## Configuration

### Backend Environment Variables

```
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_WEBHOOK_SECRET=your-webhook-secret
```

### Vapi Configuration

Set Vapi webhook URL to your Supabase Edge Function endpoint, which forwards to:

```
https://your-backend.com/vapi/webhooks
```

## Migration from Old Architecture

### ✅ Completed

- [x] Removed duplicate `webhook_handler.py`
- [x] Consolidated webhook logic into `vapi_webhook_router.py`
- [x] Updated `main.py` with dedicated `/vapi/webhooks` endpoint
- [x] Removed webhook endpoints from `voice/api.py`
- [x] Added legacy endpoint redirect for compatibility

### 🔄 Legacy Support

- Legacy `/webhooks` endpoint redirects to `/vapi/webhooks`
- Maintains backward compatibility for existing integrations
- Can be removed after all integrations are updated

## Testing

### Test Vapi Webhook

```bash
curl -X POST http://localhost:8000/vapi/webhooks \
  -H "Content-Type: application/json" \
  -d '{"message": {"type": "tool-calls"}, "call": {"id": "test-call"}}'
```

### Test Health Check

```bash
curl -X GET http://localhost:8000/vapi/webhooks
```

### Test Legacy Redirect

```bash
curl -X POST http://localhost:8000/webhooks \
  -H "Content-Type: application/json" \
  -d '{"message": {"type": "tool-calls"}}'
```

## Next Steps

1. **Set up Supabase Edge Function** to route Vapi webhooks
2. **Configure Vapi** to send webhooks to Supabase (not directly to backend)
3. **Test the integration** end-to-end
4. **Remove legacy redirect** after migration is complete
5. **Add monitoring** for webhook processing latency

## File Structure (After Consolidation)

```
backend/
├── main.py                           # ✅ /vapi/webhooks endpoint
├── services/
│   ├── voice/
│   │   ├── vapi_webhook_router.py   # ✅ Consolidated voice webhook logic
│   │   ├── api.py                   # ✅ User-facing voice endpoints only
│   │   └── webhook_handler.py       # ❌ REMOVED
│   └── user/
│       └── api.py                   # ✅ Contains auth webhook handler (separate)
```

This architecture provides a clean, focused webhook endpoint specifically for Vapi integrations while maintaining the consolidated processing logic.
