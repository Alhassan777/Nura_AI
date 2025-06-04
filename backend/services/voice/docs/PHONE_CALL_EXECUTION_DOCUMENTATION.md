# Nura Voice Assistant - Phone Call Execution Documentation

## 📞 Overview

The Nura Voice Assistant system has **complete outbound phone call capabilities** to automatically call users at their registered checkup times. This enables:

- **Scheduled Safety Checkups**: Automated calls to users at predetermined times
- **Crisis Follow-up**: Outbound calls after crisis interventions
- **Recurring Wellness Checks**: Regular mental health check-ins
- **Appointment Reminders**: Voice reminders for therapy or medical appointments

---

## 🏗️ Phone Call Architecture

### **Call Execution Flow**

```
Scheduled Time → Queue Worker → Vapi API → User's Phone → Voice Assistant Conversation
```

### **System Components**

1. **Schedule Worker** (`queue_worker.py`): Monitors due schedules
2. **Redis Queue**: Manages call jobs with retry logic
3. **Vapi Client** (`vapi_client.py`): Creates outbound calls via Vapi API
4. **Database Tracking**: Records all call attempts and outcomes

---

## 🕐 Scheduled Call System

### **1. Schedule Creation**

Users can schedule recurring voice checkups through multiple methods:

#### **Via Voice Assistant**

```
User: "Can you call me every Monday at 2 PM to check on my anxiety?"
Assistant: Calls create_schedule_appointment tool
Result: Schedule stored in database with cron expression "0 14 * * 1"
```

#### **Via Safety Network Integration**

```python
# Schedule safety checkup with contact
result = await scheduler.schedule_safety_checkup(
    user_id="user_123",
    contact_id="contact_456",
    checkup_type=CheckupType.WELLNESS_CHECK,
    method=CheckupMethod.VOICE_CALL,
    frequency="weekly",
    time_of_day="afternoon"
)
```

#### **Via API Endpoint**

```bash
curl -X POST http://localhost:8000/api/voice/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Anxiety Check-in",
    "assistant_id": "assistant_123",
    "cron_expression": "0 14 * * 1",
    "phone_number": "+1234567890",
    "metadata": {"checkup_type": "anxiety_support"}
  }' \
  --data-urlencode "user_id=user_123"
```

### **2. Background Scheduler**

The `ScheduleWorker` runs continuously:

```python
class ScheduleWorker:
    def __init__(self):
        self.check_interval = 60  # Check every 60 seconds

    async def _check_schedules(self):
        """Find schedules that are due to execute"""
        current_time = datetime.utcnow()

        # Query database for due schedules
        schedules = db.query(VoiceSchedule).filter(
            VoiceSchedule.is_active == True,
            VoiceSchedule.next_run_at <= current_time
        ).all()

        # Enqueue calls for each due schedule
        for schedule in schedules:
            await self.queue.enqueue_scheduled_call(schedule.id)
```

### **3. Call Queue Management**

Redis-based job queue with reliability features:

```python
async def enqueue_scheduled_call(self, schedule_id: str) -> str:
    """Enqueue a call from a schedule"""

    # Get schedule and user details
    schedule = db.query(VoiceSchedule).filter_by(id=schedule_id).first()
    user = db.query(VoiceUser).filter_by(id=schedule.user_id).first()

    # Create job data
    job_data = {
        "type": "outbound_call",
        "user_id": schedule.user_id,
        "assistant_id": schedule.assistant_id,
        "phone_number": user.phone,
        "metadata": {
            "schedule_id": schedule_id,
            "scheduled_call": True,
            "checkup_type": schedule.custom_metadata.get("checkup_type")
        }
    }

    # Add to Redis queue
    await redis_client.zadd(
        f"{self.queue_name}:delayed",
        {json.dumps(job_data): current_timestamp}
    )
```

---

## 📱 Outbound Call Execution

### **1. Vapi API Integration**

The system uses Vapi's REST API to create outbound calls:

```python
async def create_outbound_call(
    self,
    assistant_id: str,
    phone_number: str,  # User's registered phone number
    user_id: str,
    custom_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create an outbound phone call via Vapi API"""

    payload = {
        "assistantId": assistant_id,  # Configured Vapi assistant
        "phoneNumber": phone_number,  # User's phone in E.164 format (+1234567890)
        "metadata": {
            "userId": user_id,
            "channel": "phone",
            "callType": "scheduled_checkup",
            **custom_metadata
        }
    }

    # Call Vapi API
    response = await httpx.post(
        f"{self.base_url}/call",
        headers={"Authorization": f"Bearer {self.api_key}"},
        json=payload
    )

    return response.json()  # Returns call ID and status
```

### **2. Call Workflow**

When Vapi executes the outbound call:

1. **Phone Call Initiated**: Vapi calls the user's registered phone number
2. **Call Connection**: User answers, Vapi connects them to the voice assistant
3. **Assistant Greeting**: Voice assistant starts with contextual greeting
4. **Checkup Conversation**: Assistant conducts the scheduled checkup
5. **Tool Usage**: Assistant can use all 20 available tools during the call
6. **Call Completion**: Assistant ends call, summary stored in database

### **3. Example Call Conversation**

```
Assistant: "Hi [User Name], this is your scheduled wellness check-in.
          I'm calling as planned to see how you're doing with your anxiety management.
          How have you been feeling since our last conversation?"

User: "I've been pretty stressed about work lately."
```
