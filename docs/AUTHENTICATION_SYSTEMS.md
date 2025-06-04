# 🔐 Nura Authentication Systems

This document explains the 3 separate authentication systems implemented in Nura for different purposes.

## 📋 **Overview**

1. **Supabase Authentication** (`utils/supabase_auth.py`) - User login to Nura platform
2. **Redis Authentication** (`utils/redis_auth.py`) - Secure access to short-term memory
3. **Pinecone Authentication** (`utils/pinecone_auth.py`) - Secure access to long-term memory

---

## 🌐 **1. Supabase Authentication**

**Purpose**: Verify user identity when logging into the Nura platform.

**File**: `backend/utils/supabase_auth.py`

### Usage

```python
from utils.supabase_auth import get_authenticated_user_id
from fastapi import Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/protected-route")
async def protected_route(user_id: str = Depends(get_authenticated_user_id)):
    return {"message": f"Hello user {user_id}"}
```

### Environment Variables

```bash
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Features

- ✅ JWT token validation with Supabase
- ✅ User verification in normalized database
- ✅ Session management
- ✅ Service role detection

---

## 💾 **2. Redis Authentication (Short-term Memory)**

**Purpose**: Secure access to user's short-term memory data stored in Redis.

**File**: `backend/utils/redis_auth.py`

### Usage

```python
from utils.redis_auth import secure_redis_operation

# Get user's memories
memories = await secure_redis_operation(
    user_id="user123",
    operation="get_user_memories"
)

# Store new memory
await secure_redis_operation(
    user_id="user123",
    operation="store_memory",
    memory_data={"content": "User said hello", "type": "chat"}
)

# Get memory statistics
stats = await secure_redis_operation(
    user_id="user123",
    operation="get_stats"
)
```

### Environment Variables

```bash
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=optional_redis_password
REDIS_AUTH_SECRET=your_redis_auth_secret
REDIS_SESSION_TTL=3600  # 1 hour
```

### Features

- ✅ HMAC-based access tokens
- ✅ User-specific data isolation
- ✅ Time-based token expiration
- ✅ Automatic memory trimming
- ✅ Operation-specific scopes

---

## 🧠 **3. Pinecone Authentication (Long-term Memory)**

**Purpose**: Secure access to user's long-term memory vectors stored in Pinecone.

**File**: `backend/utils/pinecone_auth.py`

### Usage

```python
from utils.pinecone_auth import secure_pinecone_operation

# Semantic search in user's memories
results = await secure_pinecone_operation(
    user_id="user123",
    operation="search",
    query_text="What did I say about work?",
    embedding_function=get_embeddings,
    top_k=5
)

# Store new vector
await secure_pinecone_operation(
    user_id="user123",
    operation="store",
    vector_id="memory_456",
    vector_data=[0.1, 0.2, 0.3, ...],  # 768-dim vector
    metadata={"content": "Important memory", "type": "reflection"}
)

# Get vector statistics
stats = await secure_pinecone_operation(
    user_id="user123",
    operation="stats"
)
```

### Environment Variables

```bash
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=nura-memories
PINECONE_AUTH_SECRET=your_pinecone_auth_secret
PINECONE_SESSION_TTL=7200  # 2 hours
```

### Features

- ✅ Vector-specific access tokens
- ✅ User data isolation with filters
- ✅ Semantic search capabilities
- ✅ Vector ownership verification
- ✅ Scope-based permissions

---

## 🔗 **Integration Example**

Here's how to use all 3 systems together in a chat endpoint:

```python
from fastapi import APIRouter, Depends
from utils.supabase_auth import get_authenticated_user_id
from utils.redis_auth import secure_redis_operation
from utils.pinecone_auth import secure_pinecone_operation

router = APIRouter()

@router.post("/chat")
async def chat_with_memory(
    message: str,
    user_id: str = Depends(get_authenticated_user_id)  # Supabase auth
):
    # 1. Get recent short-term memories from Redis
    recent_memories = await secure_redis_operation(
        user_id=user_id,
        operation="get_user_memories"
    )

    # 2. Search long-term memories in Pinecone
    relevant_memories = await secure_pinecone_operation(
        user_id=user_id,
        operation="search",
        query_text=message,
        embedding_function=get_embeddings,
        top_k=3
    )

    # 3. Process chat with context...
    response = generate_response(message, recent_memories, relevant_memories)

    # 4. Store new memory in Redis
    await secure_redis_operation(
        user_id=user_id,
        operation="store_memory",
        memory_data={
            "content": f"User: {message}\nAssistant: {response}",
            "type": "chat_exchange"
        }
    )

    return {"response": response}
```

---

## 🛡️ **Security Features**

### Common Security Measures

- **User Isolation**: Each system ensures users can only access their own data
- **Token Expiration**: All tokens have configurable TTL
- **HMAC Signatures**: Cryptographic verification of token integrity
- **Operation Scopes**: Different permissions for read/write/delete operations

### System-Specific Security

**Supabase Auth**:

- JWT signature verification
- Audience validation
- Database user verification

**Redis Auth**:

- User-specific key namespacing
- Memory size limits
- Automatic cleanup

**Pinecone Auth**:

- Vector ownership verification
- Metadata filtering
- Index isolation

---

## 🚀 **Quick Setup**

1. **Install Dependencies**:

   ```bash
   pip install PyJWT redis pinecone-client
   ```

2. **Set Environment Variables**:

   ```bash
   # Supabase
   export SUPABASE_JWT_SECRET="your_jwt_secret"

   # Redis
   export REDIS_URL="redis://localhost:6379"
   export REDIS_AUTH_SECRET="your_redis_secret"

   # Pinecone
   export PINECONE_API_KEY="your_pinecone_key"
   export PINECONE_INDEX_NAME="nura-memories"
   export PINECONE_AUTH_SECRET="your_pinecone_secret"
   ```

3. **Import and Use**:
   ```python
   from utils.supabase_auth import get_authenticated_user_id
   from utils.redis_auth import secure_redis_operation
   from utils.pinecone_auth import secure_pinecone_operation
   ```

---

## 🔧 **Configuration**

Each authentication system can be configured via environment variables:

| System       | Variable               | Default  | Description                |
| ------------ | ---------------------- | -------- | -------------------------- |
| **Supabase** | `SUPABASE_JWT_SECRET`  | Required | JWT verification secret    |
| **Redis**    | `REDIS_SESSION_TTL`    | 3600     | Token expiration (seconds) |
| **Pinecone** | `PINECONE_SESSION_TTL` | 7200     | Token expiration (seconds) |

---

## 📝 **Best Practices**

1. **Always authenticate users first** with Supabase before accessing memory systems
2. **Use appropriate scopes** for each operation (read vs write vs delete)
3. **Handle token expiration** gracefully in your application
4. **Log security events** for audit purposes
5. **Rotate secrets regularly** in production environments

---

This architecture ensures that:

- ✅ **Users are properly authenticated** to use the platform
- ✅ **Memory data is isolated** per user
- ✅ **Access is time-limited** and scope-specific
- ✅ **Security is layered** with multiple verification steps
