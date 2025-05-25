# Nura Memory System Setup Guide

## 🚀 Quick Start: Making Your Application Memory-Ready

### 1. Environment Configuration

Create a `.env` file in your project root with the following variables:

```bash
# === REQUIRED: Core Configuration ===
GOOGLE_API_KEY=your_gemini_api_key_here
REDIS_URL=redis://localhost:6379

# === REQUIRED: Memory Scoring Prompts ===
MEMORY_COMPREHENSIVE_SCORING_PROMPT="You are a mental health memory assessment system. Analyze the following message for therapeutic value and emotional anchors..."

# === OPTIONAL: Advanced Features ===
# Google Cloud (for Vertex AI vector storage)
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1

# Memory Configuration
MEMORY_MIN_SCORE=0.6
MEMORY_MAX_SHORT_TERM=10
MEMORY_VECTOR_STORE_PATH=./data/vector_store

# Logging
LOG_LEVEL=INFO
```

### 2. Required Services Setup

#### A. Redis (Short-term Memory)

```bash
# Install Redis locally
brew install redis  # macOS
# or
sudo apt-get install redis-server  # Ubuntu

# Start Redis
redis-server

# Test connection
redis-cli ping  # Should return "PONG"
```

#### B. ChromaDB (Long-term Memory)

Already included in your requirements.txt - no additional setup needed!

### 3. Integration Code

#### A. Basic Memory Service Integration

```python
# In your main application file
import asyncio
from src.services.memory.memoryService import MemoryService
from src.services.memory.types import MemoryItem
from datetime import datetime
import uuid

# Initialize memory service
memory_service = MemoryService()

# Example: Store a user message
async def store_user_message(user_id: str, message: str):
    """Store a user message in memory system."""
    memory_item = MemoryItem(
        id=str(uuid.uuid4()),
        userId=user_id,
        content=message,
        type="user_message",
        timestamp=datetime.utcnow(),
        metadata={"source": "chat"}
    )

    # This will automatically:
    # 1. Run through QuickFilter (ML-based pre-screening)
    # 2. Score with Gemini if approved
    # 3. Detect PII and ask for consent if needed
    # 4. Store in Redis (short-term) and/or ChromaDB (long-term)
    result = await memory_service.store_memory(memory_item)
    return result

# Example: Get conversation context
async def get_conversation_context(user_id: str, current_message: str):
    """Get relevant memories for context."""
    context = await memory_service.get_conversation_context(
        user_id=user_id,
        current_message=current_message,
        max_memories=5
    )
    return context
```

#### B. FastAPI Integration Example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
memory_service = MemoryService()

class ChatMessage(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    memory_stored: bool
    context_used: list

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_msg: ChatMessage):
    try:
        # Get conversation context
        context = await get_conversation_context(
            chat_msg.user_id,
            chat_msg.message
        )

        # Generate response using your AI model + context
        response = await generate_ai_response(
            message=chat_msg.message,
            context=context
        )

        # Store user message
        user_memory_result = await store_user_message(
            chat_msg.user_id,
            chat_msg.message
        )

        # Store AI response
        ai_memory_result = await store_user_message(
            chat_msg.user_id,
            response
        )

        return ChatResponse(
            response=response,
            memory_stored=user_memory_result.get("stored", False),
            context_used=[m.content for m in context]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. Memory Flow in Your Application

```
User Message → QuickFilter → Gemini Scoring → PII Detection → Storage Decision
     ↓              ↓             ↓              ↓              ↓
   1ms filter    2-3s scoring   Privacy check   User consent   Redis + ChromaDB
   (90% accuracy) (therapeutic   (granular      (per-item)     (dual strategy)
                   value)         control)
```

### 5. API Endpoints Available

Your memory system provides these endpoints:

```python
# Health and Configuration
GET  /health                    # System status
GET  /config/test              # Configuration validation

# Core Memory Operations
POST /memory/store             # Store a memory
GET  /memory/{user_id}         # Get user memories
POST /memory/search            # Semantic search
DELETE /memory/{memory_id}     # Delete specific memory

# Privacy and Consent
POST /memory/pii/detect        # Detect PII in content
POST /memory/pii/consent       # Handle user consent
GET  /memory/pii/options       # Get consent options

# Advanced Features
POST /memory/dual-storage      # Dual storage strategy
GET  /memory/context           # Get conversation context
```

### 6. Testing Your Setup

#### A. Basic Functionality Test

```python
# test_memory_integration.py
import asyncio
from src.services.memory.memoryService import MemoryService

async def test_memory_system():
    memory_service = MemoryService()

    # Test message storage
    result = await store_user_message(
        user_id="test_user_123",
        message="I'm feeling anxious about my upcoming presentation"
    )

    print(f"Memory stored: {result}")

    # Test context retrieval
    context = await get_conversation_context(
        user_id="test_user_123",
        current_message="How can I manage my anxiety?"
    )

    print(f"Context retrieved: {len(context)} memories")

# Run test
asyncio.run(test_memory_system())
```

#### B. ML Models Test

```bash
# Test the QuickFilter with ML models
python test_quick_filter_live.py
```

### 7. Production Considerations

#### A. Environment Variables for Production

```bash
# Production .env
REDIS_URL=redis://your-redis-cluster:6379
GOOGLE_CLOUD_PROJECT=your-production-project
MEMORY_VECTOR_STORE_PATH=/app/data/vector_store
LOG_LEVEL=WARNING
MEMORY_MIN_SCORE=0.7  # Higher threshold for production
```

#### B. Scaling Considerations

- **Redis**: Use Redis Cluster for high availability
- **ChromaDB**: Consider hosted vector databases for scale
- **ML Models**: Models will download ~2GB on first run
- **Logging**: Configure structured logging for monitoring

### 8. Privacy Compliance

The system includes:

- ✅ **Granular Consent**: Per-item privacy controls
- ✅ **Dual Storage**: Different privacy levels for short/long-term
- ✅ **PII Detection**: 10+ categories of sensitive data
- ✅ **User Control**: Complete transparency and choice
- ✅ **Data Minimization**: Only stores therapeutically valuable content

### 9. Monitoring and Logs

Key metrics to monitor:

```python
# Example logging setup
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Monitor these metrics:
# - Memory storage rate
# - QuickFilter efficiency
# - PII detection accuracy
# - User consent patterns
# - System performance
```

### 10. Next Steps

1. **Set up environment variables** (step 1)
2. **Start Redis server** (step 2A)
3. **Test basic integration** (step 6A)
4. **Integrate with your chat system** (step 3B)
5. **Test with real conversations** (step 6B)
6. **Configure production settings** (step 7)

## 🆘 Troubleshooting

### Common Issues:

**Redis Connection Failed**

```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server
```

**ML Models Not Loading**

```bash
# Install ML dependencies
pip install -r requirements-ml.txt

# Check disk space (models need ~2GB)
df -h
```

**Environment Variables Missing**

```bash
# Check configuration
python -c "from src.services.memory.config import get_config; print(get_config())"
```

**PII Detection Issues**

```bash
# Test PII detection
python -c "from src.services.memory.privacy.pii_detector import PIIDetector; detector = PIIDetector(); print(detector.detect('My name is John'))"
```

## 📞 Support

If you encounter issues:

1. Check the logs for detailed error messages
2. Verify all environment variables are set
3. Test individual components separately
4. Review the comprehensive documentation in `NURA_MEMORY_SYSTEM_PROGRESS.md`

Your memory system is now ready for production use! 🚀
