# Nura Backend Database Architecture Documentation

## Overview

The Nura backend employs a sophisticated multi-database architecture designed for scalability, performance, and data isolation. The system uses multiple specialized databases and storage systems, each optimized for specific use cases in mental health support and conversation management.

## Database Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NURA DATABASE ECOSYSTEM                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │   SUPABASE      │  │     REDIS       │  │  VECTOR STORES  │                 │
│  │  (PostgreSQL)   │  │   (Caching)     │  │ (Pinecone/Chrome│                 │
│  │                 │  │                 │  │                 │                 │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │                 │
│  │ │  Frontend   │ │  │ │ Short-term  │ │  │ │ Long-term   │ │                 │
│  │ │    Auth     │ │  │ │   Memory    │ │  │ │  Memories   │ │                 │
│  │ │ Gamification│ │  │ │   Cache     │ │  │ │ Embeddings  │ │                 │
│  │ │   Users     │ │  │ │ Sessions    │ │  │ │  Semantic   │ │                 │
│  │ └─────────────┘ │  │ └─────────────┘ │  │ │   Search    │ │                 │
│  │                 │  │                 │  │ └─────────────┘ │                 │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │                 │                 │
│  │ │   Backend   │ │  │ │ API Request │ │  │                 │                 │
│  │ │  Services   │ │  │ │   Caching   │ │  │                 │                 │
│  │ │             │ │  │ │             │ │  │                 │                 │
│  │ │• Chat       │ │  │ │             │ │  │                 │                 │
│  │ │• Voice      │ │  │ │             │ │  │                 │                 │
│  │ │• User Mgmt  │ │  │ │             │ │  │                 │                 │
│  │ │• Safety Net │ │  │ │             │ │  │                 │                 │
│  │ │• Scheduling │ │  │ │             │ │  │                 │                 │
│  │ │• Audit      │ │  │ │             │ │  │                 │                 │
│  │ └─────────────┘ │  │ └─────────────┘ │  │                 │                 │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 1. Primary Database: Supabase PostgreSQL

### Configuration

- **Type**: PostgreSQL (managed by Supabase)
- **Environment Variables**:
  - `SUPABASE_DATABASE_URL`: Complete connection string
  - `SUPABASE_DB_HOST`, `SUPABASE_DB_PORT`, `SUPABASE_DB_NAME`, `SUPABASE_DB_USER`, `SUPABASE_DB_PASSWORD`: Individual connection components
- **Connection Pool**: 10-20 connections with connection recycling

### Database Schemas

#### Frontend Schema (Supabase Native)

Used by the Next.js frontend with Supabase client libraries.

**Tables:**

- `users` (Supabase Auth native table)

  - User authentication and profile data
  - Managed by Supabase Auth service
  - Extended with custom profile fields

- `user_profiles` (Custom table)

  - Additional user profile information
  - Links to Supabase auth users via `user_id`

- `reflections` (Gamification system)

  - User daily reflections
  - Mood tracking and notes
  - XP and streak calculations

- `badges` (Gamification system)
  - Achievement definitions
  - Threshold configurations for unlocking

**Frontend Database Usage:**

```typescript
// Server-side Supabase client
import { createClient } from "@/utils/supabase/server";

// Browser-side Supabase client
import { createClient } from "@/utils/supabase/client";

// Authentication integration
const {
  data: { user },
} = await supabase.auth.getUser();
```

#### Backend Schema (SQLAlchemy Models)

Used by Python backend services through SQLAlchemy ORM.

### Chat Service Tables

**`chat_users`** - User management for chat service

```sql
CREATE TABLE chat_users (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR NOT NULL,
    phone_number VARCHAR,
    password_hash VARCHAR NOT NULL,
    privacy_settings JSON DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_chat_users_email ON chat_users(email);
```

**`conversations`** - Chat session management

```sql
CREATE TABLE conversations (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL REFERENCES chat_users(id),
    title VARCHAR,
    description TEXT,
    session_type VARCHAR DEFAULT 'chat',
    status VARCHAR DEFAULT 'active',
    crisis_level VARCHAR DEFAULT 'none',
    safety_plan_triggered BOOLEAN DEFAULT FALSE,
    message_count INTEGER DEFAULT 0,
    total_duration_minutes FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_conversations_user_updated ON conversations(user_id, updated_at);
CREATE INDEX idx_conversations_status ON conversations(status);
```

**`messages`** - Individual chat messages

```sql
CREATE TABLE messages (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR NOT NULL REFERENCES conversations(id),
    user_id VARCHAR NOT NULL REFERENCES chat_users(id),
    content TEXT NOT NULL,
    role VARCHAR NOT NULL, -- 'user', 'assistant', 'system'
    message_type VARCHAR DEFAULT 'text',
    processed_content TEXT, -- PII-processed version
    pii_detected JSON DEFAULT '{}',
    sentiment_score FLOAT,
    crisis_indicators JSON DEFAULT '{}',
    requires_intervention BOOLEAN DEFAULT FALSE,
    memory_extracted BOOLEAN DEFAULT FALSE,
    memory_items_created JSON DEFAULT '[]',
    response_time_ms INTEGER,
    model_used VARCHAR,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_user ON messages(user_id);
CREATE INDEX idx_messages_created ON messages(created_at);
```

**`memory_items`** - Extracted memories from conversations

```sql
CREATE TABLE memory_items (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL REFERENCES chat_users(id),
    conversation_id VARCHAR REFERENCES conversations(id),
    message_id VARCHAR REFERENCES messages(id),
    content TEXT NOT NULL,
    processed_content TEXT,
    memory_type VARCHAR NOT NULL,
    storage_type VARCHAR DEFAULT 'short_term',
    significance_level VARCHAR DEFAULT 'low',
    significance_category VARCHAR,
    relevance_score FLOAT DEFAULT 0.0,
    stability_score FLOAT DEFAULT 0.0,
    explicitness_score FLOAT DEFAULT 0.0,
    composite_score FLOAT DEFAULT 0.0,
    embedding JSON, -- Vector embedding as JSON array
    pii_detected JSON DEFAULT '{}',
    user_consent JSON DEFAULT '{}',
    anonymized_version TEXT,
    extraction_metadata JSON DEFAULT '{}',
    tags JSON DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_memory_items_user ON memory_items(user_id);
CREATE INDEX idx_memory_items_type ON memory_items(memory_type);
CREATE INDEX idx_memory_items_storage_type ON memory_items(storage_type);
```

**`conversation_summaries`** - AI-generated conversation summaries

```sql
CREATE TABLE conversation_summaries (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR NOT NULL UNIQUE REFERENCES conversations(id),
    user_id VARCHAR NOT NULL REFERENCES chat_users(id),
    summary TEXT NOT NULL,
    key_topics JSON DEFAULT '[]',
    emotional_themes JSON DEFAULT '[]',
    action_items JSON DEFAULT '[]',
    sentiment_overall VARCHAR,
    crisis_indicators JSON DEFAULT '{}',
    therapeutic_progress JSON DEFAULT '{}',
    summary_metadata JSON DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conversation_summaries_user ON conversation_summaries(user_id);
```

**`system_events`** - Audit logging and system events

```sql
CREATE TABLE system_events (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR REFERENCES chat_users(id),
    event_type VARCHAR NOT NULL,
    event_category VARCHAR NOT NULL,
    event_data JSON DEFAULT '{}',
    severity VARCHAR DEFAULT 'info',
    session_id VARCHAR,
    ip_address VARCHAR,
    user_agent VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_events_type_created ON system_events(event_type, created_at);
CREATE INDEX idx_events_category_created ON system_events(event_category, created_at);
CREATE INDEX idx_events_severity ON system_events(severity);
```

### Voice Service Tables

**`voice_users`** - Voice service user management

```sql
CREATE TABLE voice_users (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    phone VARCHAR,
    password_hash VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**`voice_calls`** - Voice call sessions

```sql
CREATE TABLE voice_calls (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL REFERENCES voice_users(id),
    assistant_id VARCHAR NOT NULL,
    vapi_call_id VARCHAR UNIQUE,
    phone_number VARCHAR,
    status VARCHAR DEFAULT 'pending',
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    call_metadata JSON,
    transcript TEXT,
    summary TEXT,
    sentiment_analysis JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**`voice_schedules`** - Scheduled voice calls

```sql
CREATE TABLE voice_schedules (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL REFERENCES voice_users(id),
    assistant_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    cron_expression VARCHAR NOT NULL,
    timezone VARCHAR DEFAULT 'UTC',
    next_run_at TIMESTAMP NOT NULL,
    last_run_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    custom_metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Central User Service Tables

**`users`** - Centralized user management

```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR UNIQUE NOT NULL,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    phone_number VARCHAR,
    password_hash VARCHAR NOT NULL,
    privacy_settings JSON DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE,
    voice_metadata JSON DEFAULT '{}',
    chat_metadata JSON DEFAULT '{}'
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created ON users(created_at);
```

### Safety Network Service Tables

**`safety_contacts`** - Emergency contacts and trusted friends

```sql
CREATE TABLE safety_contacts (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL, -- FK to central users table
    contact_user_id VARCHAR, -- FK to users table if contact is also a system user
    external_first_name VARCHAR,
    external_last_name VARCHAR,
    external_phone_number VARCHAR,
    external_email VARCHAR,
    priority_order INTEGER NOT NULL,
    allowed_communication_methods JSON NOT NULL,
    preferred_communication_method VARCHAR NOT NULL,
    relationship_type VARCHAR,
    notes TEXT,
    preferred_contact_time VARCHAR,
    timezone VARCHAR DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Scheduling Service Tables

**`schedules`** - Unified scheduling for chat and voice assistants

```sql
CREATE TABLE schedules (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    description TEXT,
    schedule_type VARCHAR NOT NULL, -- 'chat_checkup', 'voice_call', 'reminder'
    cron_expression VARCHAR NOT NULL,
    timezone VARCHAR DEFAULT 'UTC',
    next_run_at TIMESTAMP NOT NULL,
    last_run_at TIMESTAMP,
    reminder_method VARCHAR NOT NULL, -- 'call', 'sms', 'email'
    phone_number VARCHAR,
    email VARCHAR,
    assistant_id VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    custom_metadata JSON,
    context_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 2. Redis Cache Database

### Configuration

- **Type**: Redis (in-memory key-value store)
- **Environment Variable**: `REDIS_URL` (default: redis://localhost:6379)
- **Purpose**: Caching, session management, short-term memory storage

### Redis Usage Patterns

#### Short-term Memory Storage

```python
# Memory items stored as JSON in Redis lists
key_pattern = f"user:{user_id}:memories"
# List operations: LPUSH, LRANGE, LTRIM, LREM
```

#### API Request Caching

```python
# Cached API responses and computed results
key_pattern = f"cache:{service}:{endpoint}:{hash}"
# Standard GET/SET with TTL
```

#### Session Management

```python
# User session data
key_pattern = f"session:{session_id}"
# User authentication state and preferences
```

#### Conversation Context

```python
# Recent conversation context for AI responses
key_pattern = f"user:{user_id}:context"
# Recent messages and conversation state
```

### Redis Data Structures Used

- **Lists**: Short-term memories, message queues
- **Strings**: Cached API responses, session tokens
- **Hashes**: User preferences, configuration data
- **Sets**: User tags, active sessions

## 3. Vector Databases

### Configuration

The system supports two vector database options:

#### Option 1: Pinecone (Production Recommended)

- **Environment Variables**:
  - `VECTOR_DB_TYPE=pinecone`
  - `PINECONE_API_KEY`: API key from Pinecone
  - `PINECONE_INDEX_NAME`: Index name (default: nura-memories)
  - `USE_PINECONE=true`

#### Option 2: ChromaDB (Local Development)

- **Environment Variables**:
  - `VECTOR_DB_TYPE=chroma`
  - `CHROMA_PERSIST_DIR`: Local storage directory (default: ./chroma)

### Vector Database Schema

#### Memory Embeddings

```python
# Document structure in vector database
{
    "id": "memory_uuid",
    "embedding": [0.1, 0.2, ...], # 768-dimensional vector
    "metadata": {
        "user_id": "user_uuid",
        "content": "memory content",
        "type": "personal_fact|emotional_state|goal",
        "timestamp": "2024-01-01T00:00:00Z",
        "significance_level": "low|moderate|high|critical"
    }
}
```

#### Embedding Models

- **Pinecone**: NVIDIA llama-text-embed-v2 (768 dimensions)
- **ChromaDB**: Google Gemini embedding-001 (768 dimensions)

### Vector Operations

- **Add Memory**: Store new memory with embedding
- **Semantic Search**: Find similar memories using cosine similarity
- **Update Memory**: Modify existing memory and re-embed
- **Delete Memory**: Remove memory from vector store
- **Bulk Operations**: Clear all user memories, get memory count

## 4. Database Relationships and Data Flow

### Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │     Backend     │    │    Databases    │
│   (Next.js)     │    │   (FastAPI)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌────▼────┐             ┌────▼────┐             ┌────▼────┐
    │Supabase │             │Chat     │             │Supabase │
    │Client   │             │Service  │             │PostgreSQL│
    │         │             │         │             │         │
    │• Auth   │             │• Message│             │• Users  │
    │• Profile│             │• Memory │             │• Chats  │
    │• Badges │             │• Crisis │             │• Memories│
    └─────────┘             └─────┬───┘             └─────────┘
                                  │
                             ┌────▼────┐             ┌─────────┐
                             │Memory   │             │ Redis   │
                             │Service  │◄──────────► │ Cache   │
                             │         │             │         │
                             │• Extract│             │• Short  │
                             │• Score  │             │• Session│
                             │• Store  │             │• Context│
                             └─────┬───┘             └─────────┘
                                   │
                              ┌────▼────┐             ┌─────────┐
                              │Vector   │             │Pinecone/│
                              │Store    │◄──────────► │ChromaDB │
                              │         │             │         │
                              │• Embed  │             │• Long   │
                              │• Search │             │• Semantic│
                              │• Retrieve│             │• Similar│
                              └─────────┘             └─────────┘
```

### Service-Database Mapping

| Service            | Primary Database    | Secondary Storage   | Purpose                           |
| ------------------ | ------------------- | ------------------- | --------------------------------- |
| **Frontend**       | Supabase PostgreSQL | -                   | User auth, profiles, gamification |
| **Chat Service**   | Supabase PostgreSQL | Redis (caching)     | Conversations, messages, users    |
| **Memory Service** | Vector DB + Redis   | Supabase (metadata) | Memory processing and storage     |
| **Voice Service**  | Supabase PostgreSQL | Redis (sessions)    | Voice calls, scheduling           |
| **User Service**   | Supabase PostgreSQL | -                   | Centralized user management       |
| **Safety Network** | Supabase PostgreSQL | -                   | Emergency contacts                |
| **Scheduling**     | Supabase PostgreSQL | Redis (job queue)   | Automated reminders               |
| **Audit Service**  | Supabase PostgreSQL | -                   | System events, security logs      |

### Cross-Database Relationships

#### User Identity Synchronization

```
Frontend Supabase Auth Users ←→ Backend chat_users ←→ Central users table
                             ←→ voice_users
                             ←→ safety_contacts.user_id
```

#### Memory Pipeline

```
1. Chat Message (PostgreSQL)
   ↓
2. Extract Memory (Memory Service)
   ↓
3. Short-term Storage (Redis)
   ↓
4. Process & Score (AI/ML)
   ↓
5. Long-term Storage (Vector DB)
   ↓
6. Metadata Storage (PostgreSQL)
```

#### Crisis Detection Flow

```
1. Message Analysis (Chat Service)
   ↓
2. Crisis Indicators Detected
   ↓
3. Safety Network Lookup (PostgreSQL)
   ↓
4. Emergency Contact Notification
   ↓
5. Audit Log Entry (PostgreSQL)
```

## 5. Database Configuration by Environment

### Development Environment

```bash
# Supabase (Primary)
SUPABASE_DATABASE_URL=postgresql://postgres:password@localhost:54322/postgres

# Redis (Caching)
REDIS_URL=redis://localhost:6379

# Vector Database (Local)
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIR=./data/vector_store
```

### Production Environment

```bash
# Supabase (Primary)
SUPABASE_DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# Redis (Managed)
REDIS_URL=redis://[REDIS-HOST]:6379

# Vector Database (Managed)
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=[API-KEY]
PINECONE_INDEX_NAME=nura-memories-prod
```

## 6. Database Performance and Optimization

### Indexing Strategy

#### PostgreSQL Indexes

- **Users**: email, phone_number, active status, creation date
- **Conversations**: user_id + updated_at (composite), status
- **Messages**: conversation_id, user_id, creation_at
- **Memory Items**: user_id, memory_type, storage_type
- **System Events**: event_type + created_at, category + created_at

#### Redis Optimization

- **Memory Management**: LRU eviction policy
- **Connection Pooling**: Redis connection pool with max 10 connections
- **TTL Strategy**: Auto-expire cached data after 1 hour

#### Vector Database Optimization

- **Pinecone**: Serverless tier with auto-scaling
- **ChromaDB**: HNSW index for approximate nearest neighbor search
- **Embedding Dimensions**: Consistent 768 dimensions across all models

### Connection Pooling

```python
# PostgreSQL (SQLAlchemy)
pool_size=10
max_overflow=20
pool_pre_ping=True
pool_recycle=3600

# Redis
max_connections=10
retry_on_timeout=True
```

## 7. Data Privacy and Security

### PII Detection and Management

- **Detection**: Automated PII scanning in messages and memories
- **Storage**: Separate anonymized versions of sensitive content
- **User Control**: User consent management for each memory item
- **Compliance**: GDPR-compliant data handling and deletion

### Encryption

- **At Rest**: Database-level encryption (Supabase managed)
- **In Transit**: TLS/SSL for all database connections
- **Application**: Password hashing with bcrypt

### Access Control

- **Row Level Security**: Supabase RLS policies for user data isolation
- **Service Isolation**: Each service has its own database credentials
- **API Security**: JWT-based authentication between frontend and backend

## 8. Backup and Disaster Recovery

### Supabase PostgreSQL

- **Automated Backups**: Daily automated backups with 7-day retention
- **Point-in-Time Recovery**: Available for last 24 hours
- **Cross-Region Replication**: Available in production tier

### Redis

- **Data Persistence**: RDB snapshots every 15 minutes
- **AOF Logging**: Append-only file for data recovery
- **Cluster Setup**: Redis cluster for high availability in production

### Vector Databases

- **Pinecone**: Managed backup and replication by Pinecone
- **ChromaDB**: File-based persistence with regular backups to cloud storage

## 9. Monitoring and Alerts

### Database Health Monitoring

- **Connection Pool Monitoring**: Track active/idle connections
- **Query Performance**: Slow query logging and analysis
- **Storage Usage**: Disk space and memory utilization
- **Error Rate Tracking**: Database connection errors and timeouts

### Performance Metrics

- **Response Time**: Database query latency
- **Throughput**: Queries per second per service
- **Cache Hit Rate**: Redis cache effectiveness
- **Vector Search Latency**: Embedding search performance

## 10. Migration and Schema Evolution

### Database Migrations

- **Alembic**: SQLAlchemy-based migrations for PostgreSQL schemas
- **Version Control**: All schema changes tracked in git
- **Rollback Strategy**: Automated rollback procedures for failed migrations

### Data Migration Between Environments

- **Development → Staging**: Automated data seeding scripts
- **Staging → Production**: Blue-green deployment with data validation
- **Cross-Service Sync**: User ID synchronization between services

## Conclusion

The Nura backend database architecture provides a robust, scalable foundation for mental health support services. The multi-database approach ensures optimal performance for different data types while maintaining data consistency and user privacy. The combination of PostgreSQL for structured data, Redis for caching, and vector databases for semantic search creates a comprehensive system capable of handling complex AI-driven mental health applications.

Key strengths of this architecture:

- **Scalability**: Each database optimized for its specific use case
- **Performance**: Caching and indexing strategies for fast response times
- **Privacy**: Comprehensive PII detection and user consent management
- **Reliability**: Backup and disaster recovery procedures
- **Flexibility**: Support for both local development and cloud production environments
