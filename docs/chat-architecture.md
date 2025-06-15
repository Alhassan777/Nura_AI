# Multi-Modal Chat Architecture with Multi-Layered Caching

## 🎯 Overview

This document outlines the architecture for a high-performance, multi-modal mental health chat system that achieves **ChatGPT-like response speeds** (50-200ms) while maintaining rich context awareness and supporting specialized interaction modes.

## 🏗️ Architecture Components

### **Core Principles**

1. **Immediate Response**: Users get instant feedback (50-200ms)
2. **Rich Context**: Full memory integration without speed penalties
3. **Mode Specialization**: Three distinct chat experiences
4. **Background Processing**: Heavy operations don't block user interaction
5. **Progressive Enhancement**: Context gets richer over time

## 🔄 Request Flow

```
User Message → [Mode Detection] → [Fast Response] → [Background Processing]
     ↓
[Multi-Layer Cache Check] → [Context Assembly] → [Response Generation]
     ↓
[Return to User] + [Background Tasks: Memory + Mode-Specific Processing]
```

## 🎭 Three Chat Modes

### **1. General Mode**

- **Purpose**: Pure emotional support and validation
- **System Prompt**: `system_prompt_general.txt`
- **Response Time**: 50-150ms
- **Background Processing**: Memory storage + crisis assessment
- **Features**: Active listening, validation, coping strategies, resource guidance

### **2. Action Plan Mode**

- **Purpose**: Solution-oriented collaborative planning
- **System Prompt**: `system_prompt_action_plan.txt`
- **Response Time**: 50-200ms
- **Background Processing**: Memory + action plan generation
- **Features**: Goal setting, structured planning, progress tracking

### **3. Visualization Mode**

- **Purpose**: Creative expression and emotional visualization
- **System Prompt**: `system_prompt_visualization.txt`
- **Response Time**: 50-200ms
- **Background Processing**: Memory + image generation
- **Features**: Emotional art creation, visual metaphors, creative therapy

## 🏪 Multi-Layered Caching System

### **Layer 1: Raw Data Cache (Redis)**

```typescript
interface RawDataCache {
  // Conversation context (4-hour TTL)
  conversation_messages: {
    key: `conversation:${conversationId}:messages`;
    data: MemoryItem[];
    ttl: 14400; // 4 hours
  };

  // Semantic search results (5-minute TTL)
  semantic_search_results: {
    key: `semantic_search:${userId}:${queryHash}`;
    data: MemoryItem[];
    ttl: 300; // 5 minutes
  };

  // User profile cache (1-hour TTL)
  user_profile: {
    key: `user_profile:${userId}`;
    data: UserProfile;
    ttl: 3600; // 1 hour
  };
}
```

### **Layer 2: Processed Results Cache (Redis)**

```typescript
interface ProcessedCache {
  // Processed conversation context (4-minute TTL)
  processed_conversation: {
    key: `processed_conversation:${conversationId}`;
    data: string; // Formatted context string
    ttl: 240; // 4 minutes
  };

  // Processed long-term context (5-minute TTL)
  processed_longterm: {
    key: `processed_longterm:${userId}:${queryHash}`;
    data: string; // Formatted long-term context
    ttl: 300; // 5 minutes
  };

  // Crisis assessment cache (2-minute TTL)
  crisis_assessment: {
    key: `crisis_assessment:${messageHash}`;
    data: CrisisAssessment;
    ttl: 120; // 2 minutes
  };
}
```

### **Layer 3: Combined Context Cache (Redis)**

```typescript
interface ContextCache {
  // Full enriched context (3-minute TTL)
  enriched_context: {
    key: `enriched_context:${userId}:${contextHash}`;
    data: MemoryContext;
    ttl: 180; // 3 minutes
  };

  // Mode-specific context (3-minute TTL)
  mode_context: {
    key: `mode_context:${mode}:${userId}:${contextHash}`;
    data: string; // Mode-optimized context
    ttl: 180; // 3 minutes
  };

  // Generated artifacts cache (10-minute TTL)
  action_plans: {
    key: `action_plan:${userId}:${planHash}`;
    data: ActionPlan;
    ttl: 600; // 10 minutes
  };

  image_prompts: {
    key: `image_prompt:${userId}:${promptHash}`;
    data: string;
    ttl: 600; // 10 minutes
  };
}
```

## ⚡ Performance Targets

| Component               | Current   | Target       | Improvement     |
| ----------------------- | --------- | ------------ | --------------- |
| **Pinecone Search**     | 1-3s      | 10-50ms      | **60x faster**  |
| **Context Processing**  | 100-300ms | 5-20ms       | **15x faster**  |
| **Response Generation** | 500ms-1s  | 100-200ms    | **3-5x faster** |
| **Total Response**      | 2-5s      | **50-200ms** | **20x faster**  |

## 🔄 Implementation Phases

### **Phase 1: Core Infrastructure**

- ✅ Multi-layer caching system
- ✅ Fast context retrieval methods
- ✅ Mode detection and routing
- ✅ Background task processing

### **Phase 2: General Mode**

- ✅ Immediate response generation
- ✅ Background memory processing
- ✅ Crisis detection optimization
- ✅ Context cache warming

### **Phase 3: Action Plan Mode**

- ✅ Solution-oriented responses
- ✅ Background plan generation
- ✅ Plan caching and retrieval
- ✅ Collaborative features

### **Phase 4: Visualization Mode**

- ✅ Creative response generation
- ✅ Background image creation
- ✅ Visual prompt caching
- ✅ Art therapy integration

### **Phase 5: Optimization**

- ✅ Performance monitoring
- ✅ Cache hit rate optimization
- ✅ Memory usage management
- ✅ Error handling and fallbacks

## 🛠️ Technical Implementation

### **Cache Management Strategy**

```python
class CacheManager:
    def __init__(self):
        self.ttl_strategy = {
            "semantic_search_results": 300,    # 5 min - Pinecone data stable
            "processed_conversation": 240,     # 4 min - Matches conversation TTL
            "enriched_context": 180,           # 3 min - Most dynamic
            "user_profile": 3600,              # 1 hour - Slow changing
        }

    async def get_with_fallback(self, cache_keys: List[str], fallback_func):
        """Try cache layers in order, fallback to function"""
        for key in cache_keys:
            cached = await self.get_cached(key)
            if cached and self.is_fresh(cached):
                return cached

        # Cache miss - execute fallback
        result = await fallback_func()
        await self.cache_result(cache_keys[0], result)
        return result
```

### **Query Similarity Hashing**

```python
def generate_query_hash(query: str, user_id: str) -> str:
    """Generate hash for query similarity matching"""
    # Normalize query (remove stop words, handle synonyms)
    normalized = normalize_query(query)

    # Include user context for personalization
    combined = f"{user_id}:{normalized}"

    # Generate short hash
    return hashlib.sha256(combined.encode()).hexdigest()[:16]

def normalize_query(query: str) -> str:
    """Normalize queries for better cache hits"""
    # "I'm feeling anxious" → "feeling anxious"
    # "I feel worried" → "feeling anxious" (synonym mapping)
    # "How do I cope?" → "coping strategies"
    pass
```

## 📊 Cache Invalidation Rules

```python
invalidation_rules = {
    "new_user_message": [
        "conversation_cache",
        "enriched_context"
    ],
    "conversation_end": [
        "conversation_cache",
        "processed_conversation"
    ],
    "memory_update": [
        "semantic_search_cache",
        "enriched_context"
    ],
    "user_profile_change": [
        "user_profile_cache",
        "enriched_context"
    ]
}
```

## 🚨 Error Handling & Fallbacks

### **Graceful Degradation**

1. **Cache Miss**: Fall back to database/Pinecone
2. **Pinecone Down**: Use conversation context only
3. **Redis Down**: Direct database access (slower but functional)
4. **Memory Service Down**: Generate response without context
5. **Assistant Error**: Provide empathetic fallback response

### **Circuit Breaker Pattern**

```python
class ServiceCircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```

## 🔒 Security Considerations

- **User Isolation**: All cache keys include user_id
- **JWT Authentication**: All endpoints require valid JWT tokens
- **Data Encryption**: Sensitive data encrypted in transit and at rest
- **Cache Expiration**: Automatic cleanup of expired data
- **Access Control**: Users can only access their own data

## 📈 Monitoring & Metrics

### **Performance Metrics**

- Response time percentiles (p50, p95, p99)
- Cache hit rates by layer
- Background task completion rates
- Error rates by service component

### **User Experience Metrics**

- Time to first response
- Conversation completion rates
- User satisfaction scores
- Crisis intervention response times

## 🎯 Success Criteria

1. **Speed**: 95% of responses under 200ms
2. **Reliability**: 99.9% uptime for core chat functionality
3. **Context Quality**: Maintain rich context without speed penalty
4. **Mode Effectiveness**: Each mode provides specialized value
5. **Scalability**: Handle 1000+ concurrent users
6. **Crisis Response**: Sub-second crisis detection and intervention

---

This architecture provides the foundation for a world-class mental health chat experience that is both lightning-fast and deeply contextual.
