# Vapi Local Development Guide

## 🏠 Setting Up Local Development

### 1. Expose Local Server (Required for Webhooks)

**Option A: Using ngrok (Recommended)**

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start your local server first
cd backend
python -m uvicorn main:app --reload --port 8000

# In another terminal, expose port 8000
ngrok http 8000
```

**Option B: Using VS Code Tunnels**

```bash
# Install VS Code tunnel extension
code --install-extension ms-vscode.remote-tunnels

# Create tunnel
code tunnel
```

**Option C: Using Cloudflare Tunnel**

```bash
# Install cloudflared
brew install cloudflared

# Create tunnel
cloudflared tunnel --url http://localhost:8000
```

### 2. Configure Environment Variables

Create `.env` file in your backend directory:

```env
# .env
# Vapi Configuration
VAPI_API_KEY=your_vapi_api_key_here
VAPI_WEBHOOK_SECRET=your_webhook_secret_here

# Local Development URLs
LOCAL_WEBHOOK_URL=https://your-ngrok-url.ngrok.io/api/voice/webhooks
LOCAL_API_BASE_URL=https://your-ngrok-url.ngrok.io

# Database URLs (local)
DATABASE_URL=postgresql://username:password@localhost:5432/nura_dev
MEMORY_DATABASE_URL=postgresql://username:password@localhost:5432/nura_memory_dev

# External Services
GOOGLE_AI_API_KEY=your_google_ai_key
OPENAI_API_KEY=your_openai_key
```

### 3. Update Tool Registration for Local Dev

Modify the registration script for local development:

```python
# For local development, use your ngrok URL
webhook_url = "https://your-ngrok-url.ngrok.io/api/voice/webhooks"

# Update the registrar
registrar = NuraToolRegistrar(api_key)
registrar.set_webhook_url(webhook_url)
```

## 🔧 Development Workflow

### Step 1: Start Local Services

```bash
# Terminal 1: Start database (if using Docker)
docker-compose up postgres

# Terminal 2: Start FastAPI server
cd backend
source myenv/bin/activate  # or your venv
uvicorn main:app --reload --port 8000

# Terminal 3: Expose with ngrok
ngrok http 8000
```

### Step 2: Register Tools with Local Webhook

```bash
cd backend/services/voice
python register_all_nura_tools.py
# Enter your local ngrok URL when prompted
```

### Step 3: Test Webhooks Locally

```bash
# Monitor your FastAPI logs to see incoming webhooks
# Your ngrok URL will show webhook traffic
```

## 🧪 Testing Strategy

### 1. Test Individual Tools

Create test scripts for each tool category:

```python
# test_local_tools.py
import requests

def test_crisis_tool():
    """Test crisis intervention locally"""
    webhook_url = "http://localhost:8000/api/voice/webhooks"

    payload = {
        "type": "function-call",
        "functionCall": {
            "name": "query_safety_network_contacts",
            "parameters": {
                "user_id": "test_user_123",
                "crisis_level": "moderate"
            }
        }
    }

    response = requests.post(webhook_url, json=payload)
    print(f"Response: {response.status_code} - {response.json()}")

if __name__ == "__main__":
    test_crisis_tool()
```

### 2. Use Vapi Dashboard for Testing

1. Go to [Vapi Dashboard](https://dashboard.vapi.ai)
2. Create a test assistant with your registered tools
3. Use the "Test" feature with your local webhook URL

### 3. Monitor Webhook Traffic

```bash
# ngrok provides a web interface at http://127.0.0.1:4040
# View real-time webhook requests and responses
```

## 🐛 Common Issues & Solutions

### Issue 1: Webhook Not Receiving Calls

```bash
# Check if ngrok is running
curl https://your-ngrok-url.ngrok.io/health

# Verify webhook URL in Vapi tools
# Check FastAPI logs for incoming requests
```

### Issue 2: Database Connection Errors

```bash
# Verify local database is running
pg_ctl status

# Check connection string in .env
echo $DATABASE_URL
```

### Issue 3: Tool Registration Fails

```bash
# Verify API key permissions
# Check if webhook URL is accessible from internet
curl -X POST https://your-ngrok-url.ngrok.io/api/voice/webhooks
```

## 📁 Local Project Structure

```
backend/
├── .env                          # Local environment variables
├── main.py                       # FastAPI app entry point
├── services/
│   ├── voice/
│   │   ├── webhooks.py          # Webhook handlers
│   │   ├── vapi_tools.py        # Tool definitions
│   │   ├── register_all_nura_tools.py  # Registration script
│   │   └── test_local_tools.py  # Local testing scripts
│   └── ...
├── api/
│   └── voice/
│       └── webhooks/
│           └── route.py         # Webhook routing
└── utils/
    └── config.py                # Configuration management
```

## 🔄 Development to Production Migration

### 1. Environment-Specific Configuration

```python
# utils/config.py
import os
from typing import Optional

class Config:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.vapi_api_key = os.getenv("VAPI_API_KEY")
        self.webhook_url = self._get_webhook_url()

    def _get_webhook_url(self) -> str:
        if self.environment == "development":
            return os.getenv("LOCAL_WEBHOOK_URL", "http://localhost:8000/api/voice/webhooks")
        elif self.environment == "staging":
            return os.getenv("STAGING_WEBHOOK_URL", "https://staging.your-domain.com/api/voice/webhooks")
        else:  # production
            return os.getenv("PRODUCTION_WEBHOOK_URL", "https://your-domain.com/api/voice/webhooks")

config = Config()
```

### 2. Re-register Tools for Production

```bash
# When deploying to production
ENVIRONMENT=production python register_all_nura_tools.py
```

## 🚀 Quick Start Commands

```bash
# Complete local setup in one go
./scripts/setup_local_dev.sh

# Register all tools for local development
./scripts/register_local_tools.sh

# Test all webhook endpoints
./scripts/test_webhooks.sh
```

## 📞 Support

If you encounter issues:

1. Check ngrok/tunnel connectivity
2. Verify webhook URL accessibility
3. Review FastAPI logs
4. Test individual endpoints with curl
5. Check Vapi dashboard tool configuration
