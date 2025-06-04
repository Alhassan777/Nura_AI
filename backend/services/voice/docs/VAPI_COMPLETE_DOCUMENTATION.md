# Nura VAPI Integration - Complete Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Registered Tools](#registered-tools)
4. [System Flow & Pipeline](#system-flow--pipeline)
5. [Setup & Configuration](#setup--configuration)
6. [Tool Registration](#tool-registration)
7. [Webhook Handling](#webhook-handling)
8. [Call Management](#call-management)
9. [Usage Examples](#usage-examples)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The Nura application integrates with **Vapi.ai** to provide comprehensive voice assistant capabilities for mental health support. The system includes **24 specialized tools** across 6 categories, enabling the voice assistant to:

- Manage crisis interventions with safety networks
- Schedule and manage appointments and checkups
- Generate therapeutic images and visual content
- Search and store conversation memories
- Handle general conversation management
- Coordinate safety network checkups

### **🏗️ Architecture Philosophy**

- **Hybrid Approach**: Combines Vapi native tools (SMS, transfers) with custom webhook functions
- **Database Integration**: Full CRUD operations across multiple PostgreSQL databases
- **Audit Compliance**: Complete logging for mental health regulatory requirements
- **Scalable Design**: Microservices architecture with independent tool categories

### **Key Features**

- ✅ **Real-time Crisis Intervention** with SMS and call transfer
- ✅ **Automated Scheduling** with cron-based recurring calls
- ✅ **Memory Integration** for conversation context
- ✅ **Image Generation** for emotional reflection
- ✅ **Safety Network Management** for ongoing support
- ✅ **Database Integration** across multiple PostgreSQL databases
- ✅ **Redis Queue System** for reliable call scheduling
- ✅ **Comprehensive Webhook Handling** for all tool types

You have access to twenty-four specialized tools across six categories. Use them naturally based on conversation context, not forced or robotic tool calling.

---

## 🏛️ Architecture

### **System Components**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vapi.ai       │    │   Nura Backend  │    │   Databases     │
│                 │    │                 │    │                 │
│ • Voice AI      │◄──►│ • Webhook       │◄──►│ • Voice DB      │
│ • Native Tools  │    │   Handlers      │    │ • Scheduling    │
│ • Function Calls│    │ • Tool Managers │    │ • Safety Net    │
│ • Phone Calls   │    │ • Queue Workers │    │ • Memory Store  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Call Flow Pipeline**

1. **Inbound/Outbound Call** → Vapi assistant answers
2. **Conversation Analysis** → AI determines if tools are needed
3. **Tool Execution** → Calls appropriate tools (native or webhook)
4. **Database Operations** → CRUD operations via webhooks
5. **Response Generation** → AI provides contextual response
6. **Call Completion** → Summary stored (no transcript for privacy)

---

## 🛠️ Registered Tools

### **1. 🚨 Crisis Intervention Tools (4 tools)**

**Purpose**: Handle mental health crisis situations with safety network integration

| Tool Name                       | Type              | Description                                         |
| ------------------------------- | ----------------- | --------------------------------------------------- |
| `query_safety_network_contacts` | Function          | Get emergency contacts from safety network database |
| `log_crisis_intervention`       | Function          | Record crisis intervention for follow-up            |
| `send_crisis_sms`               | SMS (Native)      | Send urgent SMS to emergency contacts               |
| `transfer_to_emergency_contact` | Transfer (Native) | Transfer call to emergency contact                  |

**Workflow Example**:

```
Crisis Detected → Query Contacts → Send SMS/Transfer Call → Log Intervention
```

### **2. 🗂️ General Voice Tools (4 tools)**

**Purpose**: Universal conversation management and system status checking across all contexts

| Tool Name             | Type              | Description                                        |
| --------------------- | ----------------- | -------------------------------------------------- |
| `end_call`            | EndCall (Native)  | End conversation naturally or for emergencies      |
| `pause_conversation`  | Function          | Temporarily pause for user processing              |
| `transfer_call`       | Transfer (Native) | General purpose call transfer                      |
| `check_system_status` | Function          | Verify if recent operations completed successfully |

**Key Features**:

- **Flexible End Call**: Replaces crisis-specific end call with general purpose
- **Contextual Reasons**: Different end call reasons (emergency, natural completion, etc.)
- **Transfer Options**: Professional therapy, peer support, technical support
- **Status Verification**: Check if operations succeeded to provide appropriate user feedback

**Status Checking Workflow**:

```
1. User requests operation (memory, scheduling, etc.)
2. Assistant performs operation using appropriate tool
3. Assistant uses `check_system_status` to verify success
4. If success: "Perfect! That's all set for you."
5. If failure: "I experienced a technical issue and I'm sorry about that."
```

### **3. 📅 Scheduling Tools (5 tools)**

**Purpose**: Comprehensive appointment and schedule management

| Tool Name                     | Type     | Description                  |
| ----------------------------- | -------- | ---------------------------- |
| `create_schedule_appointment` | Function | Create new appointments      |
| `list_user_schedules`         | Function | View user's schedule         |
| `update_schedule_appointment` | Function | Modify existing appointments |
| `delete_schedule_appointment` | Function | Cancel appointments          |
| `check_user_availability`     | Function | Check time slot availability |

**Database**: Voice scheduling PostgreSQL database with full CRUD operations

### **4. 🛡️ Safety Checkup Tools (3 tools)**

**Purpose**: Recurring wellness checks with safety network coordination

| Tool Name                      | Type     | Description                       |
| ------------------------------ | -------- | --------------------------------- |
| `schedule_safety_checkup`      | Function | Schedule recurring wellness calls |
| `get_safety_checkup_schedules` | Function | View existing checkup schedules   |
| `cancel_safety_checkup`        | Function | Cancel recurring checkups         |

**Integration**: Bridges safety network contacts with voice scheduling system

### **5. 🎨 Image Generation Tools (5 tools)**

**Purpose**: Therapeutic visual content creation and emotional processing

| Tool Name                      | Type     | Description                         |
| ------------------------------ | -------- | ----------------------------------- |
| `process_drawing_reflection`   | Function | Analyze user drawings for therapy   |
| `validate_visualization_input` | Function | Validate therapeutic image requests |
| `generate_visual_prompt`       | Function | Create image generation prompts     |
| `create_emotional_image`       | Function | Generate emotion-based imagery      |
| `get_image_generation_status`  | Function | Check image generation progress     |

**Features**: AI-powered therapeutic image generation with emotional analysis

### **6. 🧠 Memory Tools (3 tools)**

**Purpose**: Conversation memory and user context management

| Tool Name                   | Type     | Description                          |
| --------------------------- | -------- | ------------------------------------ |
| `search_user_memories`      | Function | Find relevant past conversations     |
| `store_conversation_memory` | Function | Save important conversation elements |
| `get_memory_insights`       | Function | Analyze conversation patterns        |

**Storage**: Vector database with semantic search capabilities

---

## 🔄 System Flow & Pipeline

### **Conversation to Database Pipeline**

```mermaid
graph TD
    A[User Speaks] --> B[Vapi AI Analysis]
    B --> C{Tool Needed?}
    C -->|Yes| D[Determine Tool Type]
    C -->|No| E[Continue Conversation]

    D --> F{Tool Category}
    F -->|Crisis| G[Crisis Handler]
    F -->|Schedule| H[Schedule Handler]
    F -->|Memory| I[Memory Handler]
    F -->|Image| J[Image Handler]
    F -->|Safety| K[Safety Handler]
    F -->|General| L[General Handler]

    G --> M[Safety Network DB]
    H --> N[Voice Schedule DB]
    I --> O[Memory Vector DB]
    J --> P[Image Generation API]
    K --> Q[Safety Network + Schedule DB]
    L --> R[Call Management]

    M --> S[Response to User]
    N --> S
    O --> S
    P --> S
    Q --> S
    R --> S
```

### **Crisis Intervention Workflow**

```
🚨 Crisis Detected
   ↓
1. query_safety_network_contacts (Get emergency contacts)
   ↓
2. send_crisis_sms (Vapi native SMS)
   ↓
3. transfer_to_emergency_contact (Vapi native transfer)
   ↓
4. log_crisis_intervention (Record in database)
   ↓
5. end_call (General tool with reason="emergency_referral")
```

### **Outbound Call Workflow**

```
⏰ Scheduled Time
   ↓
1. Queue Worker checks due schedules
   ↓
2. Vapi Client initiates outbound call
   ↓
3. User answers → Voice assistant conversation
   ↓
4. Tools available for: scheduling, memory, crisis, etc.
   ↓
5. Call summary stored (no transcript for privacy)
```

---

## ⚙️ Setup & Configuration

### **1. Environment Variables**

```bash
# Vapi Configuration
VAPI_API_KEY=your_vapi_api_key
VAPI_ASSISTANT_ID=your_assistant_id
WEBHOOK_SECRET=your_webhook_secret

# Database URLs
VOICE_DATABASE_URL=postgresql://user:pass@host:5432/voice_db
SCHEDULING_DATABASE_URL=postgresql://user:pass@host:5432/scheduling_db
SAFETY_NETWORK_DATABASE_URL=postgresql://user:pass@host:5432/safety_db
MEMORY_DATABASE_URL=postgresql://user:pass@host:5432/memory_db

# Redis for Queue Management
REDIS_URL=redis://localhost:6379/0
```

### **2. Database Setup**

```bash
# Initialize all databases
cd backend/services/voice && python init_db.py
cd backend/services/scheduling && python init_db.py
cd backend/services/safety_network && python init_db.py
cd backend/services/memory && python init_db.py
```

### **3. Queue Worker Setup**

```bash
# Start queue worker for outbound calls
cd backend/services/voice
python queue_worker.py
```

---

## 🔧 Tool Registration

### **Register All Tools**

```bash
# Set your Vapi API key
export VAPI_API_KEY="your_api_key_here"

# Register all tool categories
cd backend/services/voice

python register_crisis_tools.py --api-key $VAPI_API_KEY
python register_general_tools.py --api-key $VAPI_API_KEY
python register_vapi_tools.py --api-key $VAPI_API_KEY
python register_memory_tools.py --api-key $VAPI_API_KEY
python register_image_tools.py --api-key $VAPI_API_KEY
python register_safety_checkup_tools.py --api-key $VAPI_API_KEY
```

### **Verify Registration**

```bash
# Check registered tools
curl --location 'https://api.vapi.ai/tool' \
  --header 'Authorization: Bearer YOUR_API_KEY'
```

---

## 🎯 Webhook Handling

### **Webhook Architecture**

```python
# Main webhook handler routes to specific tool handlers
webhook_handler.py
├── Crisis: crisis_webhook_handler.py
├── General: Built into main handler
├── Scheduling: scheduling_integration.py
├── Memory: Direct API calls
├── Image: image_webhook_handler.py
└── Safety: safety_checkup_webhook_handler.py
```

### **Webhook Flow**

1. **Vapi sends webhook** → `POST /api/voice/webhooks`
2. **Signature verification** → HMAC validation
3. **Event routing** → Determine tool category
4. **Handler execution** → Process tool call
5. **Database operation** → CRUD operations
6. **Response** → Send result back to Vapi

### **Error Handling**

- **Retry Logic**: Failed webhooks retry 3 times
- **Fallback**: Direct emergency numbers for crisis failures
- **Logging**: Complete audit trail in database
- **Monitoring**: Real-time alerts for critical failures

---

## 📞 Call Management

### **Outbound Call Capabilities**

The system can **automatically call users** at scheduled times:

```python
# Schedule a safety checkup call
checkup = {
    "user_id": "user123",
    "contact_phone": "+1234567890",
    "frequency": "weekly",
    "time": "14:00",
    "day_of_week": "monday"
}

# Queue worker will automatically make calls at scheduled times
```

### **Call Types**

1. **Safety Checkups**: Recurring wellness calls
2. **Appointment Reminders**: Therapy/medical reminders
3. **Crisis Follow-up**: Post-crisis check-ins
4. **Medication Reminders**: Treatment adherence calls

### **Call Reliability**

- **Retry Logic**: 3 attempts for failed calls
- **Backup Methods**: SMS if call fails
- **User Preferences**: Honor do-not-disturb settings
- **Time Zones**: Automatic timezone handling

---

## 💡 Usage Examples

### **Example 1: Crisis Intervention**

````
User: "I'm having really dark thoughts and don't know what to do"

**System Flow:**

1. Assistant detects crisis keywords
2. Calls `query_safety_network_contacts`
3. Receives emergency contact information
4. Offers to transfer call or send SMS
5. If user agrees: `transfer_to_emergency_contact` or `send_crisis_sms`
6. Logs intervention with `log_crisis_intervention`

### **Example 2: Scheduling**

**User Voice Input:** _"Can you check in with me weekly about my anxiety?"_

**System Flow:**

1. Assistant analyzes scheduling intent
2. Calls `check_user_availability` to determine preferences
3. Calls `create_schedule_appointment` with cron expression
4. Confirms schedule creation with user
5. Background scheduler will execute calls automatically

### **Example 3: Memory Integration**

**User Voice Input:** _"Remember when we talked about my therapy goals?"_

**System Flow:**

1. Assistant calls `search_user_memories` with query "therapy goals"
2. Retrieves relevant past conversations
3. Uses context to provide informed response
4. Calls `store_conversation_memory` to save current discussion

### **Example 4: Image Generation**

**User Voice Input:** _"I feel lost in a gray fog, like I can't see the path ahead"_

**System Flow:**

1. Calls `validate_visualization_input` to check suitability
2. Calls `process_drawing_reflection` to analyze emotional content
3. Calls `generate_visual_prompt` to create art prompt
4. Calls `create_emotional_image` to generate artwork
5. Presents image to user for reflection

### **Example 5: Safety Checkup**

**User Voice Input:** _"Set up weekly check-ins with my sister Sarah"_

**System Flow:**
1. Calls `schedule_safety_checkup` with contact search
2. Creates recurring voice call schedule
3. Integrates with safety network database
4. Sets up automated weekly calls to user
5. Includes option to alert Sarah if user doesn't answer

### **Example 6: General Call Management**

**User Voice Input:** _"I need to end this call now, but thank you for helping"_

**System Flow:**
1. Calls `end_call` with reason="user_request"
2. Provides warm closing message
3. Offers next steps ("Feel free to call back anytime")
4. Logs call completion for follow-up analysis

---

## 🐛 Troubleshooting

### **Common Issues**

#### **1. Tool Registration Failures**

```bash
# Check tool status
curl --location 'https://api.vapi.ai/tool' \
  --header 'Authorization: Bearer YOUR_API_KEY'

# Re-register specific tool
python register_crisis_tools.py --api-key YOUR_API_KEY
```

#### **2. Webhook Signature Errors**

```python
# Verify webhook secret is correct
WEBHOOK_SECRET = "your_secret_here"

# Check signature validation in webhook_handler.py
def verify_signature(self, payload: bytes, signature: str) -> bool:
    # Implementation should match Vapi's HMAC calculation
```

#### **3. Database Connection Issues**

```bash
# Test database connections
python -c "
from services.voice.database import get_db_session
from services.scheduling.database import get_db_session as get_sched_db
from services.safety_network.database import get_db_session as get_safety_db

with get_db_session() as db:
    print('Voice DB: Connected')
with get_sched_db() as db:
    print('Scheduling DB: Connected')
with get_safety_db() as db:
    print('Safety Network DB: Connected')
"
```

#### **4. Queue Worker Not Processing Calls**

```bash
# Check Redis connection
redis-cli ping

# Check queue worker logs
cd backend/services/voice
python queue_worker.py --verbose

# Manual queue inspection
python -c "
import redis
r = redis.from_url('redis://localhost:6379/0')
print(f'Queue length: {r.llen(\"voice_call_queue\")}')
"
```

### **Monitoring & Logging**

#### **Key Log Files**

- `backend/logs/voice_service.log`: Voice service operations
- `backend/logs/webhook_handler.log`: Webhook processing
- `backend/logs/crisis_intervention.log`: Crisis intervention activities
- `backend/logs/queue_worker.log`: Scheduled call processing

#### **Important Metrics**

- **Tool Success Rate**: % of successful tool calls
- **Crisis Response Time**: Time from detection to intervention
- **Call Completion Rate**: % of successful outbound calls
- **Database Connection Health**: Connection pool status
- **Queue Processing Rate**: Jobs processed per minute

### **Emergency Procedures**

#### **Crisis Tool Failure**

If crisis tools fail:

1. **Immediate Fallback**: Direct emergency numbers (911, 988)
2. **Manual Intervention**: Admin notification system
3. **Backup Communication**: SMS/email to safety contacts
4. **Escalation**: Healthcare provider notification

#### **System-Wide Failure**

```bash
# Emergency shutdown
pkill -f "queue_worker.py"
systemctl stop nginx  # If using nginx
docker-compose down    # If using Docker

# Health check endpoints
curl http://localhost:8000/health
curl http://localhost:8000/voice/health
```

### **Performance Optimization**

#### **Database Query Optimization**

```sql
-- Ensure proper indexes exist
CREATE INDEX idx_voice_calls_user_id ON voice_calls(user_id);
CREATE INDEX idx_safety_contacts_user_emergency ON safety_contacts(user_id, is_emergency_contact);
CREATE INDEX idx_schedules_due_execution ON schedules(due_date) WHERE is_active = true;
```

#### **Webhook Response Time**

- Target: < 500ms response time
- Timeout: 5 seconds maximum
- Retries: 3 attempts with exponential backoff

---

## 📚 Additional Resources

### **Development Tools**

```bash
# Tool testing script
python tools/test_vapi_tools.py --tool crisis --user-id test_user

# Webhook simulator
python tools/webhook_simulator.py --event crisis --payload test_crisis.json

# Database migration
python tools/migrate_databases.py --version latest
```

### **Configuration Templates**

#### **Vapi Assistant Configuration**

```json
{
  "name": "Nura Mental Health Assistant",
  "model": "gpt-4",
  "voice": "sarah",
  "firstMessage": "Hi, I'm here to support you. How are you feeling today?",
  "tools": [
    // Tool IDs from registration process
    "tool_crisis_001",
    "tool_general_002",
    "tool_scheduling_003",
    // ... all 23 tool IDs
  ],
  "serverUrl": "https://your-domain.com/api/voice/webhooks",
  "endCallFunctionEnabled": true,
  "recordingEnabled": false,  // Privacy compliance
  "analysisEnabled": true
}
```

### **API Reference Links**

- [Vapi.ai Documentation](https://docs.vapi.ai/)
- [Vapi Tool API](https://docs.vapi.ai/api-reference/tools)
- [Webhook Events](https://docs.vapi.ai/webhooks)
- [Phone Number Management](https://docs.vapi.ai/phone-numbers)

### **Support Contacts**

- **Technical Issues**: tech-support@nura.ai
- **Crisis System**: crisis-support@nura.ai
- **Vapi Integration**: vapi-integration@nura.ai

---

## 🎉 Conclusion

The Nura VAPI integration provides a **comprehensive voice assistant system** with:

- ✅ **24 Specialized Tools** across 6 categories
- ✅ **Full Database Integration** with 4 PostgreSQL databases
- ✅ **Crisis Intervention System** with safety network integration
- ✅ **Automated Outbound Calls** for scheduled checkups
- ✅ **Privacy Compliance** (no transcript storage)
- ✅ **Audit Trail** for mental health compliance
- ✅ **Hybrid Architecture** (native tools + custom webhooks)

The system is **production-ready** for mental health applications requiring:
- **HIPAA compliance** (privacy-first design)
- **Crisis intervention** (immediate response capability)
- **Therapeutic tools** (image generation, memory management)
- **Care coordination** (safety networks, scheduled checkups)

For questions or support, refer to the troubleshooting section or contact the development team.

---

*Last Updated: December 2024*
*Version: 2.0 (Complete Integration)*
````
