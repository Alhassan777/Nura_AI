# Crisis Intervention System Setup Guide

## 🚨 Overview

The Crisis Intervention System **enhances** your existing crisis detection capabilities by enabling the Vapi assistant to automatically reach out to users' emergency contacts through their safety network. This integrates with your existing crisis detection prompts (`backend/utils/prompts/crisis_detection.txt` and conversation guidelines) rather than replacing them.

**Integration Flow**: Existing Crisis Protocol → Safety Network Enhancement → Emergency Contact Outreach

## 📁 File Organization

### Safety Network Service (`backend/services/safety_network/`):

- `models.py` - Database models for safety contacts
- `database.py` - Database connection management
- `manager.py` - CRUD operations for safety contacts
- `init_db.py` - Database initialization script

### Voice Service (`backend/services/voice/`):

- `vapi_crisis_tools.py` - Vapi function tool definitions
- `crisis_webhook_handler.py` - Webhook handler for Vapi tool calls
- `register_crisis_tools.py` - Tool registration script

### Prompts (`backend/utils/prompts/`):

- `crisis_detection.txt` - ✅ Existing crisis detection (keep as-is)
- `conversation_guidelines.txt` - ✅ Existing crisis protocol (keep as-is)
- `safety_network_enhancement.txt` - 🆕 New safety network enhancement

## 📋 System Requirements

- Vapi account with API access
- PostgreSQL database for safety network data
- Webhook endpoint for processing tool calls
- Existing crisis detection prompts (✅ already in `backend/utils/prompts/`)
- Optional: Twilio for SMS/calls, email service for notifications

## 🔗 Integration with Existing Crisis System

This system works **alongside** your current crisis detection:

### Current Crisis Protocol (in `conversation_guidelines.txt`):

1. ✅ Validate distress in one sentence
2. ✅ Safety check: "Are you in immediate danger?"
3. ✅ Provide crisis hotlines (988, regional numbers)
4. ✅ Encourage emergency services or trusted person contact
5. ✅ Stay present and supportive

### New Safety Network Enhancement:

6. 🆕 Query user's safety network contacts
7. 🆕 Contact first priority emergency contact
8. 🆕 Inform user about outreach
9. 🆕 Log intervention for follow-up
10. 🆕 Continue support until help arrives

## 🛠️ Setup Process

### 1. Database Initialization

First, set up the safety network database:

```bash
# Set database URL (optional - defaults to localhost)
export SAFETY_NETWORK_DATABASE_URL="postgresql://user:password@localhost:5432/nura_safety_network"

# Initialize database tables
cd backend/services/safety_network
python init_db.py
```

### 2. Register Crisis Tools with Vapi

Register the crisis intervention tools with your Vapi account:

```bash
# Navigate to voice service directory
cd backend/services/voice

# Option A: Using Python script
python register_crisis_tools.py --api-key YOUR_VAPI_API_KEY --webhook-url YOUR_WEBHOOK_URL

# Option B: Manual curl commands (see script output)
python register_crisis_tools.py  # Shows curl commands
```

### 3. Configure Vapi Assistant

Add the safety network enhancement to your assistant's system prompt (this works alongside your existing crisis detection):

```python
# Read the safety network enhancement prompt
with open('backend/utils/prompts/safety_network_enhancement.txt', 'r') as f:
    safety_network_enhancement = f.read()

# Your assistant prompt should include:
# 1. Your existing conversation guidelines (conversation_guidelines.txt)
# 2. Your existing crisis detection (crisis_detection.txt)
# 3. The new safety network enhancement (safety_network_enhancement.txt)
```

**Important**: This enhancement works with your existing crisis detection in `backend/utils/prompts/crisis_detection.txt` and the Crisis Protocol in `conversation_guidelines.txt`. Don't replace these - add the safety network tools as an additional capability.

### 4. Set Up Webhook Handler

Integrate the crisis webhook handler into your API:

```python
from voice.crisis_webhook_handler import process_vapi_crisis_webhook

# In your webhook endpoint
@app.post("/vapi/webhook")
async def vapi_webhook(request: Request):
    webhook_data = await request.json()

    # Check if this is a crisis intervention tool call
    if is_crisis_tool_call(webhook_data):
        response = await process_vapi_crisis_webhook(webhook_data)
        return response

    # Handle other tool calls...
```

## 🔧 Adding Safety Network Contacts

Users need emergency contacts in their safety network before crisis intervention can work:

```python
from safety_network.manager import SafetyNetworkManager

# Add emergency contact
contact_id = SafetyNetworkManager.add_safety_contact(
    user_id="user_123",
    first_name="John",
    last_name="Doe",
    allowed_communication_methods=["phone", "sms", "email"],
    priority_order=1,  # 1 = highest priority
    phone_number="+1234567890",
    email="john@example.com",
    relationship_type="family",
    is_emergency_contact=True,
    notes="Brother - available anytime"
)
```

## 🚨 Crisis Detection Triggers

The assistant will activate crisis intervention when it detects:

### Critical Situations (Immediate Intervention)

- Suicidal thoughts or intent
- Plans to harm self/others
- Severe panic/breakdown
- Immediate physical danger
- Complete hopelessness

### High Priority Situations (Urgent Support)

- Severe emotional distress beyond AI capabilities
- Repeated mentions of death/ending life
- Severe anxiety not responding to techniques
- Recent trauma requiring professional help
- Desperate requests for help AI cannot provide

### Moderate Situations (Human Support Beneficial)

- Repeated requests for human therapist
- Explicit need to talk to real person
- Complex situations beyond AI scope
- User stuck in crisis without progress

## 🔄 Crisis Intervention Workflow

1. **Crisis Detection**: Assistant identifies crisis situation
2. **Safety Network Query**: Query user's emergency contacts
3. **Contact Prioritization**: Select first priority contact using phone > SMS > email logic
4. **Emergency Outreach**: Contact emergency contact with crisis details
5. **User Notification**: Inform user that their contact has been notified
6. **Intervention Logging**: Log the crisis intervention for follow-up
7. **Continued Support**: Stay with user until human help arrives

## 📞 Communication Priority Logic

The system follows this priority order for crisis situations:

1. **Phone Call** (Highest Priority)

   - Immediate, real-time contact
   - Allows for immediate conversation
   - TODO: Voicemail capability for missed calls

2. **SMS** (Quick Notification)

   - Fast delivery notification
   - Works when calls can't be answered
   - Includes crisis level and brief context

3. **Email** (Documentation/Backup)
   - Detailed crisis information
   - Backup notification method
   - Creates paper trail for follow-up

## 🏗️ Architecture

```
User in Crisis → Vapi Assistant → Crisis Detection
                      ↓
              Query Safety Network Database
                      ↓
              Find First Priority Contact
                      ↓
        Initiate Contact (Phone/SMS/Email)
                      ↓
              Log Crisis Intervention
                      ↓
           Notify User & Continue Support
```

## 🔍 Tools Reference

### Tool 1: `query_safety_network_contacts`

Queries user's emergency contacts when crisis intervention is needed.

**Parameters:**

- `user_id`: User identifier
- `crisis_level`: "moderate", "high", "critical"
- `crisis_description`: Brief crisis description
- `user_current_state`: User's emotional state

### Tool 2: `initiate_emergency_contact_outreach`

Contacts the first priority emergency contact.

**Parameters:**

- `user_id`: User identifier
- `contact_id`: Emergency contact ID
- `crisis_level`: Crisis severity level
- `message_context`: Situation context for contact
- `preferred_method`: "phone", "sms", "email"

### Tool 3: `send_crisis_sms` (Vapi Built-in)

Sends SMS to emergency contact during crisis.

### Tool 4: `log_crisis_intervention`

Logs crisis intervention for record-keeping.

**Parameters:**

- `user_id`: User identifier
- `contact_id`: Contacted emergency contact ID
- `contact_method`: Method used
- `contact_success`: Whether contact was successful
- `crisis_summary`: Crisis summary
- `next_steps`: Recommended follow-up (optional)

## 🔒 Privacy & Security

- Crisis situations override normal privacy settings
- All crisis interventions are logged for audit
- Emergency contacts are only accessed during genuine crises
- User is always informed when contacts are reached
- Full transparency about crisis intervention actions

## 🚧 Current Limitations & Future Enhancements

### Current Implementation (V1)

- ✅ Contact only first priority contact once
- ✅ Support phone, SMS, email priority
- ✅ Basic crisis detection and intervention
- ✅ Full logging and audit trail

### Future Enhancements (Roadmap)

- 🔄 Escalation to multiple contacts if no response
- 🔄 Retry logic with configurable delays
- 🔄 Voicemail capability for missed calls
- 🔄 Integration with emergency services (911)
- 🔄 Real-time contact availability checking
- 🔄 Advanced crisis severity assessment
- 🔄 Integration with mental health professionals
- 🔄 Follow-up workflows and care coordination

## 🧪 Testing

### Test Crisis Scenarios

1. **User expresses suicidal thoughts**

   - Expected: Critical level crisis intervention
   - Should contact emergency contact immediately

2. **User asks for human therapist repeatedly**

   - Expected: Moderate level crisis intervention
   - Should offer to contact support network

3. **User in severe panic attack**
   - Expected: High level crisis intervention
   - Should prioritize phone contact

### Verify Implementation

```bash
# Test database connection
python -c "from safety_network.database import create_tables; create_tables()"

# Test tool registration
python register_crisis_tools.py --api-key YOUR_KEY

# Test webhook handler
# Send test webhook payload to your endpoint
```

## 📞 Emergency Fallbacks

If no emergency contacts are available:

- Direct user to call 911 for life-threatening emergencies
- Provide National Suicide Prevention Hotline: 988
- Offer Crisis Text Line: Text HOME to 741741
- Suggest local emergency services

## 📊 Monitoring & Analytics

Monitor crisis interventions through:

- `ContactLog` table for all contact attempts
- Crisis intervention logs with success rates
- Response time analytics
- Follow-up effectiveness tracking

## 🆘 Support & Troubleshooting

### Common Issues

1. **No emergency contacts found**

   - Solution: Users must add emergency contacts first
   - Fallback: Direct to emergency services

2. **Webhook not receiving calls**

   - Check webhook URL configuration
   - Verify tool registration with Vapi
   - Test endpoint accessibility

3. **Database connection issues**
   - Verify DATABASE_URL configuration
   - Check PostgreSQL service status
   - Ensure tables are initialized

### Contact for Help

- Review logs in `backend/logs/`
- Check database connectivity
- Verify Vapi API key and tool registration
- Test webhook endpoint independently

---

**⚠️ IMPORTANT**: This system handles life-critical situations. Always test thoroughly before deploying to production and ensure proper monitoring and failover mechanisms are in place.
