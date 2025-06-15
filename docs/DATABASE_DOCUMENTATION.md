# Nura Backend Database Architecture Documentation

## Overview

The Nura backend employs a **unified database architecture** using Supabase PostgreSQL as the primary database for all services. This design provides data consistency, simplified maintenance, and optimal performance through proper indexing and relationship management.

## Database Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NURA DATABASE ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │   SUPABASE      │  │     REDIS       │  │  VECTOR STORES  │                 │
│  │  (PostgreSQL)   │  │   (Caching)     │  │ (Pinecone/Chrome│                 │
│  │                 │  │                 │  │                 │                 │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │                 │
│  │ │  Frontend   │ │  │ │ Short-term  │ │  │ │ Long-term   │ │                 │
│  │ │    Auth     │ │  │ │   Memory    │ │  │ │  Memories   │ │                 │
│  │ │    Users    │ │  │ │   Cache     │ │  │ │ Embeddings  │ │                 │
│  │ │ Gamification│ │  │ │ Sessions    │ │  │ │  Semantic   │ │                 │
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
│  │ │• Memory     │ │  │ │             │ │  │                 │                 │
│  │ │• Privacy    │ │  │ │             │ │  │                 │                 │
│  │ │• Assistant  │ │  │ │             │ │  │                 │                 │
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

#### Normalized User System

**Central User Management** - Single source of truth for all user data:

```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,  -- Supabase Auth UUID
    email VARCHAR UNIQUE NOT NULL,
    phone_number VARCHAR,
    full_name VARCHAR,
    display_name VARCHAR,
    bio TEXT,
    avatar_url VARCHAR,

    -- Auth metadata (synced from Supabase)
    email_confirmed_at TIMESTAMP WITH TIME ZONE,
    phone_confirmed_at TIMESTAMP WITH TIME ZONE,
    last_sign_in_at TIMESTAMP WITH TIME ZONE,

    -- Backend-managed fields
    is_active BOOLEAN DEFAULT TRUE,
    current_streak INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,

    -- Preferences
    privacy_settings JSON DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Service-specific user profiles
CREATE TABLE user_service_profiles (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_type VARCHAR NOT NULL,  -- 'chat', 'voice', 'memory', etc.
    service_preferences JSON DEFAULT '{}',
    service_metadata JSON DEFAULT '{}',
    usage_stats JSON DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, service_type)
);
```

#### Chat Service Tables

**`conversations`** - Chat session management

```sql
CREATE TABLE conversations (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
```

**`messages`** - Individual chat messages

```sql
CREATE TABLE messages (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
```

**`memory_items`** - Extracted memories from conversations

```sql
CREATE TABLE memory_items (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id VARCHAR REFERENCES conversations(id) ON DELETE SET NULL,
    message_id VARCHAR REFERENCES messages(id) ON DELETE SET NULL,
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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    is_archived BOOLEAN DEFAULT FALSE
);
```

#### Voice Service Tables

**`voices`** - Available voice assistants

```sql
CREATE TABLE voices (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR NOT NULL,
    assistant_id VARCHAR UNIQUE NOT NULL,
    description TEXT,
    sample_url VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**`voice_calls`** - Voice call records

```sql
CREATE TABLE voice_calls (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    vapi_call_id VARCHAR UNIQUE,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assistant_id VARCHAR NOT NULL REFERENCES voices(assistant_id),
    channel VARCHAR, -- 'web', 'phone'
    status VARCHAR DEFAULT 'pending',
    phone_number VARCHAR,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cost_total DECIMAL(10,4),
    cost_breakdown JSON
);
```

**`call_summaries`** - Voice call summaries (NO transcripts)

```sql
CREATE TABLE call_summaries (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id VARCHAR NOT NULL REFERENCES voice_calls(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary_json JSON NOT NULL,
    duration_seconds INTEGER,
    sentiment VARCHAR,
    key_topics JSON DEFAULT '[]',
    action_items JSON DEFAULT '[]',
    crisis_indicators JSON DEFAULT '{}',
    emotional_state VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Safety Network Tables

**`safety_contacts`** - Emergency contacts and trusted friends

```sql
CREATE TABLE safety_contacts (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_user_id VARCHAR REFERENCES users(id) ON DELETE SET NULL,
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
    is_emergency_contact BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_contacted_at TIMESTAMP WITH TIME ZONE,
    last_contact_method VARCHAR,
    last_contact_successful BOOLEAN,
    custom_metadata JSON DEFAULT '{}'
);
```

#### Scheduling Service Tables

**`schedules`** - Unified scheduling for chat and voice assistants

```sql
CREATE TABLE schedules (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    description TEXT,
    schedule_type VARCHAR NOT NULL, -- 'chat_checkup', 'voice_call', 'reminder'
    cron_expression VARCHAR NOT NULL,
    timezone VARCHAR DEFAULT 'UTC',
    next_run_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_run_at TIMESTAMP WITH TIME ZONE,
    reminder_method VARCHAR NOT NULL, -- 'call', 'sms', 'email'
    phone_number VARCHAR,
    email VARCHAR,
    assistant_id VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    custom_metadata JSON DEFAULT '{}',
    context_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Gamification Tables

**`badges`** - Achievement definitions

```sql
CREATE TABLE badges (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR NOT NULL,
    description TEXT,
    icon_url VARCHAR,
    xp_award INTEGER DEFAULT 0,
    criteria JSON DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**`user_badges`** - User achievement tracking

```sql
CREATE TABLE user_badges (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id VARCHAR NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, badge_id)
);
```

#### Image Generation Tables

**`generated_images`** - AI-generated emotional visualization images

```sql
CREATE TABLE generated_images (
    id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR,
    prompt TEXT NOT NULL,
    image_data TEXT NOT NULL, -- base64 or URL to file
    image_format VARCHAR DEFAULT 'png',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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

## 4. Service Integration Architecture

### Data Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │     Backend     │    │    Databases    │
│   (Next.js)     │    │   (FastAPI)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌────▼────┐             ┌────▼────┐             ┌────▼────┐
    │Supabase │             │Mental   │             │Supabase │
    │Client   │             │Health   │             │PostgreSQL│
    │         │             │Assistant│             │         │
    │• Auth   │             │(Refactor│             │• Users  │
    │• Profile│             │ed)      │             │• Chat   │
    │• Badges │             │• Crisis │             │• Voice  │
    └─────────┘             │• Memory │             │• Memory │
                            │• Extract│             │• Safety │
                            └─────┬───┘             └─────────┘
                                  │
                             ┌────▼────┐             ┌─────────┐
                             │Memory   │             │ Redis   │
                             │Service  │◄──────────► │ Cache   │
                             │         │             │         │
                             │• Store  │             │• Short  │
                             │• Retriev│             │• Session│
                             │• Process│             │• Context│
                             └─────┬───┘             └─────────┘
                                   │
                              ┌────▼────┐             ┌─────────┐
                              │Vector   │             │Pinecone/│
                              │Store    │◄──────────► │ChromaDB │
                              │         │             │         │
                              │• Embed  │             │• Long   │
                              │• Search │             │• Semantic│
                              │• Similar│             │• Search │
                              └─────────┘             └─────────┘
```

### Service-Database Mapping

| Service                     | Primary Database    | Secondary Storage   | Purpose                              |
| --------------------------- | ------------------- | ------------------- | ------------------------------------ |
| **Frontend**                | Supabase PostgreSQL | -                   | User auth, profiles, gamification    |
| **Mental Health Assistant** | Supabase PostgreSQL | Redis + Vector      | Refactored assistant with extractors |
| **Chat Service**            | Supabase PostgreSQL | Redis (caching)     | Conversations, messages              |
| **Memory Service**          | Vector DB + Redis   | Supabase (metadata) | Memory processing and storage        |
| **Voice Service**           | Supabase PostgreSQL | Redis (sessions)    | Voice calls, scheduling              |
| **User Service**            | Supabase PostgreSQL | -                   | Centralized user management          |
| **Safety Network**          | Supabase PostgreSQL | -                   | Emergency contacts                   |
| **Scheduling**              | Supabase PostgreSQL | Redis (job queue)   | Automated reminders                  |
| **Image Generation**        | Supabase PostgreSQL | -                   | AI-generated emotional images        |
| **Privacy Service**         | Supabase PostgreSQL | -                   | PII detection and consent            |

## 5. Database Performance and Optimization

### Indexing Strategy

#### PostgreSQL Indexes

```sql
-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created ON users(created_at);

-- Conversations & Messages
CREATE INDEX idx_conversations_user_updated ON conversations(user_id, updated_at);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_user ON messages(user_id);
CREATE INDEX idx_messages_created ON messages(created_at);

-- Memory Items
CREATE INDEX idx_memory_items_user ON memory_items(user_id);
CREATE INDEX idx_memory_items_type ON memory_items(memory_type);
CREATE INDEX idx_memory_items_storage_type ON memory_items(storage_type);

-- Voice Service
CREATE INDEX idx_voice_calls_user ON voice_calls(user_id);
CREATE INDEX idx_call_summaries_user ON call_summaries(user_id);

-- Safety Network
CREATE INDEX idx_safety_contacts_user ON safety_contacts(user_id);
CREATE INDEX idx_safety_contacts_priority ON safety_contacts(user_id, priority_order);

-- Generated Images
CREATE INDEX idx_generated_images_user ON generated_images(user_id);
CREATE INDEX idx_generated_images_created ON generated_images(created_at);
```

#### Redis Optimization

- **Memory Management**: LRU eviction policy
- **Connection Pooling**: Redis connection pool with max 10 connections
- **TTL Strategy**: Auto-expire cached data after appropriate intervals

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

## 6. Data Privacy and Security

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
- **Service Isolation**: Each service has appropriate database permissions
- **API Security**: JWT-based authentication between frontend and backend

## 7. Backup and Disaster Recovery

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

## 8. Migration and Schema Evolution

### Database Migrations

- **Alembic**: SQLAlchemy-based migrations for PostgreSQL schemas
- **Version Control**: All schema changes tracked in git
- **Rollback Strategy**: Automated rollback procedures for failed migrations

### Data Migration Between Environments

- **Development → Staging**: Automated data seeding scripts
- **Staging → Production**: Blue-green deployment with data validation
- **User Normalization**: Ongoing migration from legacy user tables to normalized schema

## 9. Monitoring and Performance

### Key Metrics

- **Database Performance**: Query latency, connection pool utilization
- **Cache Performance**: Redis hit rates, memory usage
- **Vector Search**: Search latency, index size
- **User Data**: Growth rates, storage utilization

### Health Checks

```python
# Database health monitoring
async def check_database_health():
    # PostgreSQL connection test
    # Redis connectivity test
    # Vector database availability
    # Performance metrics collection
```

## 10. Future Scalability Considerations

### Horizontal Scaling

- **Read Replicas**: Supabase read replicas for heavy read workloads
- **Service Separation**: Individual services can scale independently
- **Cache Sharding**: Redis sharding for larger user bases

### Data Archival

- **Cold Storage**: Archive old conversations and memories
- **Data Lifecycle**: Automated data retention policies
- **Compliance**: User-controlled data deletion and export

This unified database architecture provides a robust, scalable foundation for the Nura mental health platform while maintaining data consistency, privacy, and performance across all services.
