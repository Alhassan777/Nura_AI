# API Endpoint Configuration for Vapi Tools

## 🎯 Overview

This document explains how **Vapi tools connect to your backend API endpoints** to retrieve data, create records, and perform operations. The system uses a hybrid approach with both direct database access and HTTP API calls.

## 🏗️ Architecture Types

### **Type 1: Direct Database Access (Crisis & Safety)**

```
Vapi Tool Call → Webhook Handler → Direct Database Query → Response
```

### **Type 2: HTTP API Calls (Scheduling, Memory, Images)**

```
Vapi Tool Call → Webhook Handler → HTTP Request → Your API → Database → Response
```

## 📍 API Endpoint Configuration

### **Environment Variables Setup**

Create a `.env` file in your backend directory:

```bash
# Vapi Configuration
VAPI_API_KEY=your_vapi_api_key
VAPI_ASSISTANT_ID=your_assistant_id
WEBHOOK_SECRET=your_webhook_secret

# Database URLs (for direct access)
VOICE_DATABASE_URL=postgresql://user:pass@host:5432/voice_db
SCHEDULING_DATABASE_URL=postgresql://user:pass@host:5432/scheduling_db
SAFETY_NETWORK_DATABASE_URL=postgresql://user:pass@host:5432/safety_db
MEMORY_DATABASE_URL=postgresql://user:pass@host:5432/memory_db

# API Endpoints (for HTTP calls)
SCHEDULING_API_BASE=http://localhost:8000/api/scheduling
SAFETY_NETWORK_API_BASE=http://localhost:8000/api/safety-network
MEMORY_API_BASE=http://localhost:8000/api/memory
IMAGE_GENERATION_API_BASE=http://localhost:8000/api/image-generation
USER_API_BASE=http://localhost:8000/api/user

# External APIs
OPENAI_API_KEY=sk-your-openai-key
HF_TOKEN=hf_your-huggingface-token

# Webhook Configuration
WEBHOOK_TIMEOUT=30
MAX_RETRY_ATTEMPTS=3
```

### **Production Environment Variables**

For production, change the localhost URLs:

```bash
# Production API Endpoints
SCHEDULING_API_BASE=https://your-domain.com/api/scheduling
SAFETY_NETWORK_API_BASE=https://your-domain.com/api/safety-network
MEMORY_API_BASE=https://your-domain.com/api/memory
IMAGE_GENERATION_API_BASE=https://your-domain.com/api/image-generation
USER_API_BASE=https://your-domain.com/api/user
```

## 🛠️ Tool to Endpoint Mapping

### **1. 🚨 Crisis Tools (Direct Database)**

| Tool                            | Method   | Endpoint      | Description                        |
| ------------------------------- | -------- | ------------- | ---------------------------------- |
| `query_safety_network_contacts` | Database | Direct query  | Gets emergency contacts            |
| `log_crisis_intervention`       | Database | Direct insert | Records crisis event               |
| `send_crisis_sms`               | Logging  | Database log  | Logs SMS (Vapi sends actual SMS)   |
| `transfer_to_emergency_contact` | Logging  | Database log  | Logs transfer (Vapi does transfer) |

**Implementation**:

```python
# Direct database access in crisis_webhook_handler.py
from safety_network.database import get_db_session
from safety_network.models import SafetyContact

with get_db_session() as db:
    contacts = db.query(SafetyContact).filter(...).all()
```

### **2. 📅 Scheduling Tools (HTTP API)**

| Tool                          | Method | Endpoint                                    | Description          |
| ----------------------------- | ------ | ------------------------------------------- | -------------------- |
| `create_schedule_appointment` | POST   | `/api/scheduling/schedules`                 | Creates new schedule |
| `list_user_schedules`         | GET    | `/api/scheduling/schedules?user_id={id}`    | Lists user schedules |
| `update_schedule_appointment` | PUT    | `/api/scheduling/schedules/{id}`            | Updates schedule     |
| `delete_schedule_appointment` | DELETE | `/api/scheduling/schedules/{id}`            | Deletes schedule     |
| `check_user_availability`     | GET    | `/api/scheduling/availability?user_id={id}` | Checks availability  |

**Implementation**:

```python
# HTTP API calls in scheduling_integration.py
async with aiohttp.ClientSession() as session:
    url = f"{config.get_api_endpoint('scheduling')}/schedules"
    async with session.post(url, json=data) as response:
        result = await response.json()
```

### **3. 🛡️ Safety Checkup Tools (Hybrid)**

| Tool                           | Method | Endpoint                                    | Description              |
| ------------------------------ | ------ | ------------------------------------------- | ------------------------ |
| `schedule_safety_checkup`      | POST   | `/api/safety-network/checkups`              | Creates checkup schedule |
| `get_safety_checkup_schedules` | GET    | `/api/safety-network/checkups?user_id={id}` | Lists checkups           |
| `cancel_safety_checkup`        | DELETE | `/api/safety-network/checkups/{id}`         | Cancels checkup          |

### **4. 🧠 Memory Tools (HTTP API)**

| Tool                        | Method | Endpoint                            | Description            |
| --------------------------- | ------ | ----------------------------------- | ---------------------- |
| `search_user_memories`      | POST   | `/api/memory/search`                | Semantic memory search |
| `store_conversation_memory` | POST   | `/api/memory/store`                 | Stores conversation    |
| `get_memory_insights`       | GET    | `/api/memory/insights?user_id={id}` | Memory analytics       |

### **5. 🎨 Image Generation Tools (HTTP API)**

| Tool                           | Method | Endpoint                                | Description              |
| ------------------------------ | ------ | --------------------------------------- | ------------------------ |
| `process_drawing_reflection`   | POST   | `/api/image-generation/analyze`         | Analyzes user drawings   |
| `validate_visualization_input` | POST   | `/api/image-generation/validate`        | Validates image request  |
| `generate_visual_prompt`       | POST   | `/api/image-generation/prompt`          | Creates image prompt     |
| `create_emotional_image`       | POST   | `/api/image-generation/create`          | Generates image          |
| `get_image_generation_status`  | GET    | `/api/image-generation/status/{job_id}` | Checks generation status |

### **6. 🗂️ General Tools (Native Vapi)**

| Tool                 | Method | Endpoint     | Description         |
| -------------------- | ------ | ------------ | ------------------- |
| `end_call`           | Native | Vapi handles | Ends conversation   |
| `pause_conversation` | Native | Vapi handles | Pauses conversation |
| `transfer_call`      | Native | Vapi handles | Transfers call      |

## 🔧 Implementation Examples

### **Example 1: Environment Variable Configuration**

```python
# config.py
import os

class VoiceConfig:
    def __init__(self):
        self.SCHEDULING_API_BASE = os.getenv(
            "SCHEDULING_API_BASE",
            "http://localhost:8000/api/scheduling"
        )

    def get_api_endpoint(self, service: str) -> str:
        endpoints = {
            "scheduling": self.SCHEDULING_API_BASE,
            "memory": self.MEMORY_API_BASE,
            # ... etc
        }
        return endpoints[service]
```

### **Example 2: Dynamic API Calls**

```python
# scheduling_integration.py
from .config import config

class SchedulingIntegration:
    def __init__(self):
        # Gets endpoint from environment variable
        self.api_base = config.get_api_endpoint("scheduling")

    async def handle_create_schedule(self, data):
        url = f"{self.api_base}/schedules"  # Uses configured endpoint
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                return await response.json()
```

### **Example 3: Direct Database Access**

```python
# crisis_webhook_handler.py
from safety_network.database import get_db_session

async def _handle_query_safety_contacts(parameters):
    with get_db_session() as db:
        contacts = db.query(SafetyContact).filter(
            SafetyContact.user_id == user_id
        ).all()
        return contacts
```

## 🚀 Quick Setup Guide

### **Step 1: Configure Environment**

```bash
# Copy example environment file
cp backend/.env.example backend/.env

# Edit with your endpoints
nano backend/.env
```

### **Step 2: Verify Configuration**

```python
# Test configuration
python -c "
from backend.services.voice.config import config
print('Scheduling API:', config.get_api_endpoint('scheduling'))
print('Memory API:', config.get_api_endpoint('memory'))
"
```

### **Step 3: Test API Connectivity**

```bash
# Test your scheduling API
curl -X GET "http://localhost:8000/api/scheduling/health"

# Test memory API
curl -X GET "http://localhost:8000/api/memory/health"
```

### **Step 4: Register Tools with Correct Webhooks**

```bash
# Register tools pointing to your webhook endpoint
export VAPI_API_KEY="your_api_key"
cd backend/services/voice

python register_vapi_tools.py --webhook-url "https://your-domain.com/api/voice/webhooks"
```

## 🔧 Advanced Configuration

### **Custom API Clients**

```python
# Create custom API client with authentication
class AuthenticatedAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def post(self, endpoint: str, data: dict):
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}{endpoint}"
            async with session.post(url, json=data, headers=self.headers) as response:
                return await response.json()
```

### **Load Balancing Multiple Endpoints**

```python
# Round-robin across multiple API endpoints
class LoadBalancedAPIClient:
    def __init__(self, endpoints: List[str]):
        self.endpoints = endpoints
        self.current = 0

    def get_next_endpoint(self) -> str:
        endpoint = self.endpoints[self.current]
        self.current = (self.current + 1) % len(self.endpoints)
        return endpoint
```

### **Health Check Integration**

```python
# Automatic endpoint health checking
async def check_endpoint_health(endpoint: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{endpoint}/health", timeout=5) as response:
                return response.status == 200
    except:
        return False
```

## 🐛 Troubleshooting

### **Common Issues**

1. **Connection Refused**

   ```bash
   # Check if your API is running
   curl -v http://localhost:8000/api/scheduling/health
   ```

2. **Environment Variables Not Loading**

   ```python
   # Verify environment variables
   import os
   print("SCHEDULING_API_BASE:", os.getenv("SCHEDULING_API_BASE"))
   ```

3. **Database Connection Issues**

   ```python
   # Test database connectivity
   from safety_network.database import get_db_session
   with get_db_session() as db:
       print("Database connected!")
   ```

4. **Webhook Signature Errors**
   ```python
   # Verify webhook secret matches
   print("WEBHOOK_SECRET:", os.getenv("WEBHOOK_SECRET"))
   ```

### **Logging Configuration**

```python
# Enable debug logging for API calls
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("aiohttp.client")
logger.setLevel(logging.DEBUG)
```

## 📚 Summary

Your Vapi tools connect to your APIs through:

1. **Environment Variables** - Configure endpoints dynamically
2. **Webhook Handlers** - Process tool calls and route to appropriate APIs
3. **HTTP Clients** - Make requests to your backend services
4. **Direct Database Access** - For high-performance operations

**Key Files**:

- `config.py` - Centralized endpoint configuration
- `scheduling_integration.py` - Scheduling API client
- `crisis_webhook_handler.py` - Direct database access
- `webhook_handler.py` - Main routing logic

**Next Steps**:

1. Set your environment variables
2. Test API connectivity
3. Register tools with correct webhook URL
4. Monitor logs for any connection issues

The system is designed to be **flexible** - you can easily change endpoints, add authentication, or switch between direct database access and HTTP APIs as needed.
