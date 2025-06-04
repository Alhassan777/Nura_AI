# Crisis Intervention Setup Guide

## 🚨 Overview

The Nura crisis intervention system uses a **hybrid approach** combining Vapi's native communication tools with external service fallbacks to ensure reliable emergency contact during mental health crises.

## 🏗️ Architecture

### Vapi Native Tools (Primary)

- **SMS**: Uses Vapi's built-in SMS tool for immediate text messaging
- **Call Transfer**: Uses Vapi's transferCall tool for immediate call routing
- **End Call**: Uses Vapi's endCall tool for emergency termination

### External Services (Fallback)

- **Email**: SendGrid + AWS SES (Vapi doesn't have native email)
- **SMS Backup**: Twilio (if Vapi SMS fails)
- **Call Backup**: Twilio (for outbound calling)

## 📋 Required Tools Registration

### 1. Traditional Function Tools

These handle the crisis workflow logic:

```bash
# Register via our script
cd backend/services/voice
python register_crisis_tools.py
```

**Registered Tools:**

- `query_safety_network_contacts` - Find emergency contacts
- `initiate_emergency_contact_outreach` - Coordinate outreach
- `log_crisis_intervention` - Record intervention

### 2. Vapi Native Tools

These execute actual communication:

**SMS Tool** ([Vapi SMS Documentation](https://docs.vapi.ai/api-reference/tools/create#request.body.sms)):

```json
{
  "type": "sms",
  "function": {
    "name": "send_crisis_sms",
    "description": "Send SMS to emergency contact via Vapi",
    "parameters": {
      "type": "object",
      "properties": {
        "to": { "type": "string", "description": "Phone number" },
        "message": { "type": "string", "description": "Crisis message" }
      },
      "required": ["to", "message"]
    }
  }
}
```

**Transfer Call Tool** ([Vapi Transfer Documentation](https://docs.vapi.ai/api-reference/tools/create#response.body.transferCall)):

```json
{
  "type": "transferCall",
  "function": {
    "name": "transfer_to_emergency_contact",
    "description": "Transfer call to emergency contact",
    "parameters": {
      "type": "object",
      "properties": {
        "destination": {
          "type": "object",
          "properties": {
            "type": { "type": "string", "enum": ["number"] },
            "number": { "type": "string" },
            "message": { "type": "string" }
          },
          "required": ["type", "number"]
        }
      },
      "required": ["destination"]
    }
  }
}
```

**End Call Tool** ([Vapi End Call Documentation](https://docs.vapi.ai/api-reference/tools/create#request.body.endCall)):

```json
{
  "type": "endCall",
  "function": {
    "name": "end_crisis_call",
    "description": "End call in crisis situations",
    "parameters": {
      "type": "object",
      "properties": {
        "message": { "type": "string", "description": "Final message" }
      },
      "required": ["message"]
    }
  }
}
```

## ⚙️ Environment Configuration

### Required Environment Variables

```bash
# Vapi Configuration
VAPI_API_KEY=your_vapi_api_key
VAPI_ASSISTANT_ID=your_assistant_id

# External Service Fallbacks (Optional but Recommended)
# Twilio (SMS/Call backup)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890

# SendGrid (Email)
SENDGRID_API_KEY=your_sendgrid_key
CRISIS_FROM_EMAIL=crisis@nura.app

# AWS SES (Email fallback)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
```

## 🚀 Crisis Intervention Workflow

### 1. Crisis Detection

When a user expresses distress, the assistant:

```
User: "I'm feeling suicidal and don't know what to do"
Assistant: Detects crisis → Calls query_safety_network_contacts
```

### 2. Find Emergency Contacts

```python
# Tool Call: query_safety_network_contacts
{
  "user_id": "user123",
  "crisis_level": "critical",
  "crisis_description": "User expressing suicidal ideation",
  "user_current_state": "Distressed, hopeless, needs immediate support"
}

# Response:
{
  "has_contacts": true,
  "first_priority_contact": {
    "contact_id": "contact456",
    "first_name": "Sarah",
    "relationship_type": "sister",
    "preferred_method": "phone",
    "phone_number": "+1234567890"
  }
}
```

### 3. Initiate Contact (Multiple Options)

#### Option A: Direct Call Transfer (Immediate)

```python
# Tool Call: transfer_to_emergency_contact
{
  "destination": {
    "type": "number",
    "number": "+1234567890",
    "message": "Transferring to Sarah for emergency support"
  }
}
```

#### Option B: Send Crisis SMS

```python
# Tool Call: send_crisis_sms
{
  "to": "+1234567890",
  "message": "URGENT: Your family member needs immediate support. Please call them at [user_phone]. This is a mental health crisis alert from Nura."
}
```

#### Option C: End Call (Emergency Services)

```python
# Tool Call: end_crisis_call
{
  "message": "I'm going to end this call so you can dial 911 immediately. Please call emergency services or go to your nearest emergency room. You are not alone."
}
```

### 4. Log Intervention

```python
# Tool Call: log_crisis_intervention
{
  "user_id": "user123",
  "contact_id": "contact456",
  "contact_method": "phone_transfer",
  "contact_success": true,
  "crisis_summary": "Critical crisis - transferred call to sister Sarah",
  "next_steps": "Monitor for follow-up contact from emergency contact"
}
```

## 🔧 Implementation Details

### Crisis Detection Triggers

The assistant should trigger crisis intervention when:

- **Suicidal ideation**: "I want to hurt myself", "I don't want to be here"
- **Self-harm**: "I'm cutting", "I hurt myself"
- **Severe distress**: "I can't handle this", "Everything is falling apart"
- **Hopelessness**: "Nothing matters", "There's no point"

### Contact Priority Logic

1. **Phone/Transfer**: Immediate connection for real-time support
2. **SMS**: Quick notification when calls aren't possible
3. **Email**: Fallback when other methods fail

### Tool Integration Order

```
Crisis Detected → Query Contacts → Choose Method:
├── High Urgency: transfer_to_emergency_contact (immediate)
├── Medium Urgency: send_crisis_sms (quick notification)
├── Low/No Contacts: end_crisis_call + 911 guidance
└── All Cases: log_crisis_intervention (record keeping)
```

## 🧪 Testing the System

### 1. Register All Tools

```bash
cd backend/services/voice
python register_crisis_tools.py
```

### 2. Test Crisis Flow

Use test phrases to trigger crisis detection:

```
"I'm having thoughts of hurting myself"
→ Should trigger: query_safety_network_contacts
→ If contacts found: Offer transfer_to_emergency_contact
→ Should log: log_crisis_intervention
```

### 3. Test Communication Methods

**Test Vapi SMS**:

```bash
curl -X POST "https://api.vapi.ai/tool" \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "sms",
    "function": {"name": "test_crisis_sms"}
  }'
```

**Test Call Transfer**:
Configure in Vapi assistant dashboard with transferCall tool.

## 📊 Monitoring & Analytics

### Key Metrics to Track

- **Crisis Detection Rate**: How often crises are identified
- **Contact Success Rate**: Percentage of successful emergency contacts
- **Response Time**: Time from crisis to contact attempt
- **Tool Effectiveness**: Which communication methods work best

### Logging

All crisis interventions are logged with:

- Crisis severity level
- Contact methods attempted
- Success/failure status
- Timeline of events
- Follow-up actions needed

## 🚨 Emergency Escalation

If all emergency contacts fail:

1. **Guide to Emergency Services**:

   ```
   "I wasn't able to reach your emergency contacts. Please call:
   • 911 for immediate emergency
   • 988 for Suicide & Crisis Lifeline
   • Text HOME to 741741 for Crisis Text Line"
   ```

2. **End Call Tool**: Use `end_crisis_call` to free the line for emergency calls

3. **Log Failed Attempts**: Record all failed contact attempts for follow-up

## 📞 Support & Troubleshooting

### Common Issues

1. **Vapi Tools Not Working**:

   - Check API key permissions
   - Verify tools are associated with assistant
   - Confirm webhook URL is configured

2. **External Services Failing**:

   - Verify environment variables
   - Check service API limits
   - Test credentials independently

3. **No Emergency Contacts**:
   - Guide user to create safety network
   - Provide crisis hotline numbers
   - Consider ending call for 911 access

### Support Resources

- **Crisis Hotlines**: 988, 911, Crisis Text Line (741741)
- **Documentation**: [Vapi Tools API](https://docs.vapi.ai/api-reference/tools/create)
- **Monitoring**: Check `backend.log` for detailed crisis intervention logs

---

**⚠️ Critical Safety Note**: This system assists in crisis situations but does not replace professional mental health services or emergency response. Always prioritize user safety and encourage professional help when needed.
