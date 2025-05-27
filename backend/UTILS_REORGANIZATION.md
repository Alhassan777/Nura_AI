# Utils Reorganization - Modular Backend Structure

## Overview

The backend utilities have been reorganized into a modular structure to improve maintainability, reusability, and organization. All utilities are now centralized in the `backend/utils/` directory and can be shared across all services (memory, chat, voice).

## New Structure

```
backend/
├── utils/                          # Centralized utilities
│   ├── __init__.py                 # Main exports and imports
│   ├── auth.py                     # Authentication utilities
│   ├── database.py                 # Database operations
│   ├── redis_client.py             # Redis operations and caching
│   ├── voice.py                    # Voice/Vapi integration utilities
│   ├── security.py                 # Security and sanitization
│   └── validation.py               # Input validation and sanitization
├── services/
│   ├── memory/                     # Memory service
│   ├── chat/                       # Chat service (new)
│   └── voice/                      # Voice service
└── ...
```

## Module Breakdown

### 1. `utils/auth.py` - Authentication Utilities

**Purpose**: Handle password hashing, session management, and user authentication for the localStorage-based system.

**Key Functions**:

- `hash_password()` - Secure password hashing with salt
- `verify_password()` - Password verification
- `create_session_token()` - Generate secure session tokens
- `store_session()` - Store user sessions in Redis
- `get_session()` - Retrieve and validate sessions
- `delete_session()` - Session cleanup
- `cleanup_expired_sessions()` - Maintenance function

**Usage Example**:

```python
from utils.auth import hash_password, verify_password, store_session

# Hash password for storage
hashed = hash_password("user_password")

# Verify password during login
is_valid = verify_password("user_password", hashed)

# Store session after successful login
await store_session(user_id, session_token, user_data)
```

### 2. `utils/database.py` - Database Operations

**Purpose**: Common database operations, health checks, and maintenance tasks.

**Key Functions**:

- `execute_query()` - Safe SQL query execution
- `check_database_health()` - Database connectivity checks
- `get_table_info()` - Table metadata and statistics
- `backup_table()` - Table backup operations
- `cleanup_old_records()` - Data retention management
- `get_database_stats()` - Database performance metrics

**Usage Example**:

```python
from utils.database import execute_query, check_database_health

# Execute a safe query
result = await execute_query(session, "SELECT * FROM users WHERE id = :id", {"id": user_id})

# Check database health
health = await check_database_health(session)
```

### 3. `utils/redis_client.py` - Redis Operations

**Purpose**: Centralized Redis operations for caching, session management, and data storage.

**Key Functions**:

- `cache_set()` / `cache_get()` - Basic caching operations
- `cache_list_push()` / `cache_list_get()` - List operations
- `cache_hash_set()` / `cache_hash_get()` - Hash operations
- `cache_increment()` / `cache_decrement()` - Counter operations
- `cache_cleanup_expired()` - Maintenance
- `cache_info()` - Redis statistics

**Usage Example**:

```python
from utils.redis_client import cache_set, cache_get, cache_list_push

# Cache user data
await cache_set(f"user:{user_id}", user_data, ttl_seconds=3600)

# Retrieve cached data
user_data = await cache_get(f"user:{user_id}")

# Store conversation history
await cache_list_push(f"conversation:{conv_id}", message_data, max_length=100)
```

### 4. `utils/voice.py` - Voice Integration

**Purpose**: Vapi.ai integration, call mappings, and voice-specific operations.

**Key Functions**:

- `get_customer_id()` - Retrieve user ID from call ID
- `store_call_mapping()` - Store call-to-user mappings
- `extract_call_id_from_vapi_event()` - Parse Vapi webhooks
- `store_conversation_context()` - Store call context
- `extract_user_message_from_event()` - Parse user messages

**Usage Example**:

```python
from utils.voice import store_call_mapping, get_customer_id

# Store call mapping when call starts
await store_call_mapping(call_id, user_id, mode="web")

# Retrieve user ID in webhook handler
user_id = await get_customer_id(call_id)
```

### 5. `utils/security.py` - Security Utilities

**Purpose**: Security-related functions for input sanitization, CSRF protection, and security headers.

**Key Functions**:

- `sanitize_input()` - XSS and injection prevention
- `generate_csrf_token()` / `verify_csrf_token()` - CSRF protection
- `check_password_strength()` - Password validation
- `get_security_headers()` - HTTP security headers
- `validate_webhook_signature()` - HMAC signature validation
- `mask_sensitive_data()` - Data masking for logs

**Usage Example**:

```python
from utils.security import sanitize_input, get_security_headers, check_password_strength

# Sanitize user input
clean_input = sanitize_input(user_input)

# Check password strength
strength = check_password_strength(password)

# Get security headers for responses
headers = get_security_headers()
```

### 6. `utils/validation.py` - Input Validation

**Purpose**: Input validation, sanitization, and data format checking.

**Key Functions**:

- `validate_email()` - Email format validation
- `validate_phone_number()` - Phone number validation
- `validate_user_input()` - General input validation
- `validate_conversation_data()` - Chat message validation
- `validate_uuid()` - UUID format validation
- `check_rate_limit()` - Rate limiting checks

**Usage Example**:

```python
from utils.validation import validate_user_input, validate_conversation_data

# Validate user registration data
validation = validate_user_input(form_data, ["email", "password", "full_name"])

# Validate chat message
msg_validation = validate_conversation_data(message_data)
```

## Migration from Old Structure

### Before (Scattered Utils)

```
backend/services/memory/
├── utils/
│   └── vapi.py                     # Only voice utilities
├── security/
│   └── pii_detector.py
├── storage/
│   ├── redis_store.py
│   └── vector_store.py
└── ...
```

### After (Centralized Utils)

```
backend/
├── utils/                          # All utilities centralized
│   ├── auth.py
│   ├── database.py
│   ├── redis_client.py
│   ├── voice.py
│   ├── security.py
│   └── validation.py
└── services/
    ├── memory/                     # Service-specific logic only
    ├── chat/
    └── voice/
```

## Benefits of New Structure

### 1. **Modularity**

- Each utility module has a single responsibility
- Easy to test individual components
- Clear separation of concerns

### 2. **Reusability**

- Utilities can be shared across all services
- No code duplication between services
- Consistent implementations

### 3. **Maintainability**

- Centralized location for common operations
- Easier to update and fix bugs
- Better code organization

### 4. **Scalability**

- Easy to add new utility modules
- Services can focus on business logic
- Shared infrastructure components

## Usage in Services

### Import Pattern

```python
# Import specific functions
from utils.auth import hash_password, verify_password
from utils.redis_client import cache_set, cache_get
from utils.validation import validate_email

# Or import entire modules
from utils import auth, redis_client, validation
```

### Service Integration

Each service can now focus on its core business logic while leveraging shared utilities:

```python
# In chat service
from utils.auth import get_session
from utils.validation import validate_conversation_data
from utils.redis_client import cache_set

async def send_message(session_token, message_data):
    # Validate session
    session = await get_session(session_token)

    # Validate message
    validation = validate_conversation_data(message_data)

    # Cache message
    await cache_set(f"message:{message_id}", message_data)
```

## Configuration

All utilities use environment variables for configuration, which are centralized in the `.env.example` file. This ensures consistent configuration across all services.

## Next Steps

1. **Update existing services** to use the new utils structure
2. **Remove old utility files** from service directories
3. **Add tests** for each utility module
4. **Create service-specific APIs** that leverage these utilities
5. **Implement proper error handling** and logging throughout

This reorganization provides a solid foundation for the Nura backend architecture, making it more maintainable and scalable as the application grows.
