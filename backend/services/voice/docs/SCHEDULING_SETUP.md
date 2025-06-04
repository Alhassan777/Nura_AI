# Vapi Scheduling Integration Setup

This guide explains how to set up and use the Vapi function tools for schedule management in your mental health application.

## 🏗️ Architecture Overview

```
User Voice Call → Vapi Assistant → Function Tools → Our Scheduling API → Database
```

1. **User** talks to Vapi voice assistant about scheduling
2. **Vapi Assistant** uses function tools to manage schedules
3. **Function Tools** make HTTP calls to our scheduling service
4. **Scheduling Service** manages database operations
5. **Database** stores schedule appointments

## 🚀 Setup Instructions

### 1. Environment Variables

Add these to your `.env` file:

```bash
# Vapi Configuration
VAPI_API_KEY=your_vapi_api_key
VAPI_PUBLIC_KEY=your_vapi_public_key
VAPI_SERVER_SECRET=your_vapi_server_secret
VAPI_DEFAULT_ASSISTANT_ID=your_assistant_id

# Scheduling Database
SCHEDULING_DATABASE_URL=postgresql://localhost:5432/nura_scheduling
```

### 2. Initialize Scheduling Database

```bash
# From backend directory
python -c "from services.scheduling.init_db import init_scheduling_database; import asyncio; asyncio.run(init_scheduling_database())"
```

### 3. Register Vapi Tools

#### Option A: Automated Registration

```bash
cd backend/services/voice
python register_vapi_tools.py
```

#### Option B: Manual curl Commands

```bash
python register_vapi_tools.py --curl
```

This will output curl commands you can run manually.

### 4. Start Services

```bash
# Start your backend with scheduling service
uvicorn main:app --reload --port 8000
```

## 🛠️ Available Tools

The integration creates 5 Vapi function tools:

### 1. `create_schedule_appointment`

- **Purpose**: Create new scheduled checkups
- **Parameters**: name, schedule_type, cron_expression, reminder_method, etc.
- **Example**: "Schedule weekly anxiety check-ins on Mondays at 2 PM"

### 2. `list_user_schedules`

- **Purpose**: List user's existing schedules
- **Parameters**: active_only (optional)
- **Example**: "What checkups do I have scheduled?"

### 3. `update_schedule_appointment`

- **Purpose**: Modify existing schedules
- **Parameters**: schedule_id + updated fields
- **Example**: "Change my weekly checkup to Fridays"

### 4. `delete_schedule_appointment`

- **Purpose**: Cancel scheduled checkups
- **Parameters**: schedule_id, reason (optional)
- **Example**: "Cancel my exam stress follow-up"

### 5. `check_user_availability`

- **Purpose**: Help determine optimal scheduling times
- **Parameters**: preferred_time_of_day, preferred_days, frequency
- **Example**: "I'm free weekday mornings for weekly checkups"

## 📞 Voice Assistant Usage Examples

### Creating Schedules

**User**: _"Can you check in with me weekly about my anxiety?"_

**Assistant**: _"I'd be happy to schedule regular check-ins! When would work best for you?"_

**User**: _"Maybe Monday afternoons?"_

**Assistant**: _"Perfect! I'll schedule weekly anxiety check-ins for Monday afternoons. How would you like me to remind you - by call, text, or email?"_

### Checking Schedules

**User**: _"What appointments do I have coming up?"_

**Assistant**: _"You have 2 scheduled checkups: Weekly Anxiety Check-in and Exam Stress Follow-up."_

### Canceling Schedules

**User**: _"I don't need the exam checkup anymore"_

**Assistant**: _"I've cancelled your Exam Stress Follow-up. You won't receive any more reminders for it."_

## 🔧 Configuration

### Cron Expression Examples

- Daily 9 AM: `"0 9 * * *"`
- Weekly Monday 2 PM: `"0 14 * * 1"`
- Bi-weekly Friday 10 AM: `"0 10 * * 5/2"`
- Monthly first Monday: `"0 9 1-7 * 1"`

### Schedule Types

- `chat_checkup`: Text-based checkup via chat interface
- `voice_checkup`: Phone call checkup via Vapi

### Reminder Methods

- `call`: Phone call reminder
- `sms`: Text message reminder
- `email`: Email reminder

## 🔄 Integration Flow

### When User Requests Scheduling:

1. **Chat Assistant** detects scheduling opportunity using `schedule_extraction.txt` prompt
2. **Chat Assistant** adds scheduling suggestion to response with `schedule_analysis`
3. If user agrees, **Voice Assistant** can use tools to create actual schedule
4. **Vapi Tools** call our scheduling API endpoints
5. **Schedule** stored in database with context and metadata

### When Schedule Executes:

1. **Scheduler** finds due schedules in database
2. **Reminder** sent via chosen method (call/SMS/email)
3. **Execution** logged for tracking and analytics

## 🧪 Testing

### Test Tool Registration

```bash
# Check if tools were created
curl -X GET https://api.vapi.ai/tool \
  -H "Authorization: Bearer $VAPI_API_KEY"
```

### Test Scheduling API

```bash
# Test create schedule
curl -X POST http://localhost:8000/api/scheduling/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Checkup",
    "schedule_type": "chat_checkup",
    "cron_expression": "0 14 * * 1",
    "reminder_method": "email",
    "email": "test@example.com"
  }' \
  -G -d "user_id=test_user"
```

## 🐛 Troubleshooting

### Common Issues

1. **Tools not appearing in Vapi assistant**

   - Check VAPI_API_KEY is correct
   - Verify assistant_id in environment
   - Re-run tool registration

2. **Scheduling API calls failing**

   - Check scheduling service is running on port 8000
   - Verify database connection
   - Check API endpoint URLs in vapi_tools.py

3. **Database connection errors**
   - Initialize scheduling database first
   - Check SCHEDULING_DATABASE_URL
   - Ensure PostgreSQL is running

### Logs

Check logs for detailed error information:

```bash
# Backend logs
tail -f backend.log

# Vapi webhook logs
# Check your webhook endpoint logs
```

## 🔗 Related Files

- `vapi_tools.py` - Tool definitions for Vapi
- `register_vapi_tools.py` - Tool registration script
- `scheduling_integration.py` - Integration layer
- `../scheduling/` - Scheduling service implementation
- `../../utils/prompts/schedule_extraction.txt` - Chat scheduling detection
