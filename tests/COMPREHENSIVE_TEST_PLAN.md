# 🧪 Comprehensive Test Plan for Nura Backend

## Overview

This document outlines the complete testing strategy for the Nura mental health chat application backend. The testing plan covers all API endpoints, core services, storage layers, voice integration, privacy features, and system reliability components.

## Testing Architecture

```
tests/
├── unit/                          # Unit tests for individual components
│   ├── api/                       # API endpoint tests
│   ├── services/                  # Service layer tests
│   ├── storage/                   # Storage layer tests
│   ├── security/                  # Security and privacy tests
│   └── utils/                     # Utility function tests
├── integration/                   # Integration tests
│   ├── workflows/                 # End-to-end workflow tests
│   ├── cross_service/             # Cross-service integration tests
│   └── external/                  # External API integration tests
├── performance/                   # Performance and load tests
├── fixtures/                      # Test data and fixtures
└── conftest.py                   # Pytest configuration
```

---

## 📋 **1. API Endpoints Testing**

### **1.1 Health API (`/api/health`)**

#### Test Coverage:

- **Health Check Endpoint (`GET /api/health`)**

  - ✅ Returns healthy status when all services operational
  - ✅ Returns degraded status when configuration issues exist
  - ✅ Includes correct service status information
  - ✅ Returns proper timestamp and version information
  - ✅ Handles missing environment variables gracefully

- **Configuration Validation (`GET /api/health/config/test`)**

  - ✅ Validates required environment variables (GOOGLE_API_KEY)
  - ✅ Checks vector database configuration (Pinecone vs Vertex AI)
  - ✅ Validates optional configuration files
  - ✅ Returns appropriate error messages for missing configs
  - ✅ Provides actionable recommendations for fixes

- **Service Status Monitoring (`GET /api/health/services`)**
  - ✅ Tests memory service connectivity
  - ✅ Tests voice service configuration
  - ✅ Tests Redis connection and ping
  - ✅ Returns overall status based on individual service health
  - ✅ Handles service failures gracefully

#### Test Files:

```
tests/unit/api/test_health_api.py
tests/integration/api/test_health_integration.py
```

### **1.2 Memory API (`/api/memory`)**

#### Test Coverage:

- **Memory Processing (`POST /api/memory/`)**

  - ✅ Processes different memory types (chat, user_message, assistant_response)
  - ✅ Handles PII detection and consent requirements
  - ✅ Returns appropriate response models
  - ✅ Integrates with dual storage strategy
  - ✅ Handles configuration warnings
  - ✅ Error handling for invalid requests

- **Memory Context (`POST /api/memory/context`)**

  - ✅ Retrieves memory context with and without query
  - ✅ Combines short-term and long-term memories
  - ✅ Handles semantic search functionality
  - ✅ Returns proper context structure
  - ✅ Handles empty memory scenarios

- **Memory Statistics (`GET /api/memory/stats`)**

  - ✅ Returns accurate memory counts
  - ✅ Separates short-term and long-term statistics
  - ✅ Includes sensitive memory counts
  - ✅ Handles user with no memories

- **Memory Management**

  - ✅ Delete specific memory (`DELETE /api/memory/{memory_id}`)
  - ✅ Clear all memories (`POST /api/memory/forget`)
  - ✅ Export memories (`POST /api/memory/export`)
  - ✅ Handle consent (`POST /api/memory/consent`)

- **Dual Storage Strategy**

  - ✅ Dual storage processing (`POST /api/memory/dual-storage`)
  - ✅ Dual storage consent (`POST /api/memory/dual-storage/consent`)
  - ✅ Dual storage info (`GET /api/memory/dual-storage/info`)

- **Memory Types and Categories**

  - ✅ Get emotional anchors (`GET /api/memory/emotional-anchors`)
  - ✅ Get regular memories (`GET /api/memory/regular-memories`)
  - ✅ Get all long-term memories (`GET /api/memory/all-long-term`)

- **Consent Management**
  - ✅ Get pending consent memories (`GET /api/memory/pending-consent`)
  - ✅ Process pending consent (`POST /api/memory/process-pending-consent`)
  - ✅ Session summary (`GET /api/memory/session-summary`)
  - ✅ Apply memory choices (`POST /api/memory/apply-choices`)

#### Test Files:

```
tests/unit/api/test_memory_api.py
tests/integration/api/test_memory_integration.py
tests/unit/api/test_memory_dual_storage.py
tests/unit/api/test_memory_consent.py
```

### **1.3 Chat API (`/api/chat`)**

#### Test Coverage:

- **Chat Assistant (`POST /api/chat/assistant`)**

  - ✅ Generates appropriate mental health responses
  - ✅ Integrates memory context when requested
  - ✅ Detects and handles crisis situations
  - ✅ Stores user and assistant messages in memory
  - ✅ Returns proper response structure with metadata
  - ✅ Handles configuration warnings
  - ✅ Error handling for service failures

- **Crisis Resources (`GET /api/chat/crisis-resources`)**
  - ✅ Returns comprehensive crisis resource information
  - ✅ Includes hotlines, text lines, and emergency actions
  - ✅ Provides international resources
  - ✅ Returns consistent resource structure

#### Test Files:

```
tests/unit/api/test_chat_api.py
tests/integration/api/test_chat_integration.py
tests/unit/api/test_crisis_handling.py
```

### **1.4 Privacy API (`/api/privacy`)**

#### Test Coverage:

- **Privacy Review (`GET /api/privacy/review/{user_id}`)**

  - ✅ Identifies memories containing PII
  - ✅ Analyzes PII risk levels and types
  - ✅ Provides privacy choice options
  - ✅ Handles both short-term and long-term memories
  - ✅ Skips already processed memories
  - ✅ Returns comprehensive PII analysis

- **Privacy Choices (`POST /api/privacy/apply-choices/{user_id}`)**
  - ✅ Applies "remove_entirely" choice correctly
  - ✅ Applies "remove_pii_only" with anonymization
  - ✅ Applies "keep_original" with user approval
  - ✅ Updates memory metadata appropriately
  - ✅ Handles errors gracefully
  - ✅ Returns detailed processing results

#### Test Files:

```
tests/unit/api/test_privacy_api.py
tests/integration/api/test_privacy_integration.py
tests/unit/api/test_privacy_choices.py
```

### **1.5 Voice API (`/api/voice`)**

#### Test Coverage:

- **Call Mapping Management**

  - ✅ Store call mapping (`POST /api/voice/mapping`)
  - ✅ Get call mapping (`GET /api/voice/mapping/{call_id}`)
  - ✅ Delete call mapping (`DELETE /api/voice/mapping/{call_id}`)
  - ✅ Handle TTL expiration
  - ✅ Error handling for missing mappings

- **Voice Event Processing (`POST /api/voice/process-event`)**

  - ✅ Processes Vapi webhook events
  - ✅ Extracts call and customer information
  - ✅ Integrates with memory service
  - ✅ Returns processing results with timing
  - ✅ Handles missing customer mappings

- **Webhook Handling (`POST /api/voice/webhook`)**

  - ✅ Verifies webhook signatures
  - ✅ Routes different event types appropriately
  - ✅ Processes call lifecycle events
  - ✅ Stores webhook events for audit
  - ✅ Returns appropriate responses to Vapi

- **Voice Metrics (`GET /api/voice/metrics/latency`)**
  - ✅ Returns voice processing latency metrics
  - ✅ Includes call processing statistics
  - ✅ Handles metric calculation errors

#### Test Files:

```
tests/unit/api/test_voice_api.py
tests/integration/api/test_voice_integration.py
tests/unit/api/test_voice_webhooks.py
tests/unit/api/test_voice_mapping.py
```

---

## 📋 **2. Core Services Testing**

### **2.1 MemoryService**

#### Test Coverage:

**Memory Processing:**

- ✅ `process_memory()` with different content types
- ✅ Dual storage strategy implementation
- ✅ PII detection integration during processing
- ✅ Component-based memory scoring
- ✅ Consent handling for sensitive data
- ✅ Chat vs non-chat message differentiation
- ✅ Memory metadata enrichment
- ✅ Error handling for processing failures

**Memory Retrieval:**

- ✅ `get_memory_context()` with query parameter
- ✅ `get_memory_context()` without query (recent context)
- ✅ `get_memory_stats()` accuracy
- ✅ `get_emotional_anchors()` filtering logic
- ✅ `get_regular_memories()` filtering logic
- ✅ Semantic search functionality
- ✅ Memory ranking and relevance

**Memory Management:**

- ✅ `delete_memory()` from both storage types
- ✅ `clear_memories()` complete user data removal
- ✅ Memory update operations
- ✅ Memory count tracking accuracy
- ✅ Storage type coordination

**Privacy & Consent:**

- ✅ `get_pending_consent_memories()` identification
- ✅ `process_pending_consent()` with user decisions
- ✅ `get_chat_session_summary()` for user review
- ✅ `apply_user_memory_choices()` (keep/remove/anonymize)
- ✅ Consent metadata tracking
- ✅ Privacy choice persistence

**Dual Storage Strategy:**

- ✅ Short-term vs long-term storage decisions
- ✅ PII handling differences between storage types
- ✅ Consent deferral for chat messages
- ✅ Component-based storage logic
- ✅ Storage recommendation accuracy

#### Test Files:

```
tests/unit/services/test_memory_service.py
tests/unit/services/test_memory_processing.py
tests/unit/services/test_memory_retrieval.py
tests/unit/services/test_memory_consent.py
tests/unit/services/test_dual_storage.py
```

### **2.2 MentalHealthAssistant**

#### Test Coverage:

**Response Generation:**

- ✅ `generate_response()` with memory context integration
- ✅ Response quality and appropriateness
- ✅ Memory context utilization
- ✅ Configuration warning handling
- ✅ Session metadata extraction
- ✅ Error handling and fallback responses

**Crisis Detection:**

- ✅ `_assess_crisis_level()` for different crisis indicators
- ✅ Crisis level classification (CRISIS, CONCERN, SUPPORT)
- ✅ Crisis response generation
- ✅ Safety protocol implementation
- ✅ Emergency resource provision
- ✅ Crisis flag setting for human handoff

**Context Building:**

- ✅ `_build_conversation_context()` accuracy
- ✅ Memory context integration
- ✅ Conversation history processing
- ✅ Digest generation
- ✅ Context relevance filtering

**Resource Management:**

- ✅ `provide_crisis_resources()` completeness
- ✅ Resource extraction from responses
- ✅ Coping strategy identification
- ✅ Resource categorization and prioritization

**Configuration Management:**

- ✅ Prompt loading and fallback handling
- ✅ Configuration validation
- ✅ Environment variable checking
- ✅ Degraded mode operation

#### Test Files:

```
tests/unit/services/test_mental_health_assistant.py
tests/unit/services/test_crisis_detection.py
tests/unit/services/test_response_generation.py
tests/unit/services/test_resource_management.py
```

### **2.3 PIIDetector**

#### Test Coverage:

**PII Detection:**

- ✅ `detect_pii()` with Presidio integration
- ✅ Hugging Face NER integration
- ✅ Custom pattern recognition
- ✅ Risk level classification (high/medium/low)
- ✅ PII type identification accuracy
- ✅ Confidence scoring
- ✅ False positive/negative handling

**Consent Management:**

- ✅ `get_granular_consent_options()` for detected PII
- ✅ Item-specific recommendations
- ✅ Risk-based default choices
- ✅ Consent option generation
- ✅ User choice validation

**Anonymization:**

- ✅ `apply_granular_consent()` with user choices
- ✅ Storage-type specific handling
- ✅ Placeholder generation accuracy
- ✅ Content replacement precision
- ✅ Anonymization reversibility prevention

**PII Categories:**

- ✅ High-risk PII detection (names, emails, phones, healthcare providers)
- ✅ Medium-risk PII detection (medical diagnoses, facilities)
- ✅ Low-risk PII detection (therapy types, crisis hotlines)
- ✅ Custom pattern matching
- ✅ Entity boundary detection

#### Test Files:

```
tests/unit/services/test_pii_detector.py
tests/unit/services/test_pii_anonymization.py
tests/unit/services/test_pii_consent.py
tests/unit/services/test_pii_patterns.py
```

---

## 📋 **3. Storage Layer Testing**

### **3.1 RedisStore**

#### Test Coverage:

**Memory Operations:**

- ✅ `add_memory()` with TTL and size limits
- ✅ `get_memories()` with proper ordering
- ✅ `delete_memory()` by ID accuracy
- ✅ `update_memory()` functionality
- ✅ `clear_memories()` complete removal
- ✅ `get_memory_count()` accuracy
- ✅ Memory serialization/deserialization
- ✅ Size limit enforcement

**Connection Management:**

- ✅ Redis connection establishment
- ✅ Connection pooling
- ✅ Error handling for connection failures
- ✅ Retry logic testing
- ✅ Connection timeout handling

**Data Integrity:**

- ✅ Memory data consistency
- ✅ TTL expiration behavior
- ✅ Concurrent access handling
- ✅ Memory ordering preservation

#### Test Files:

```
tests/unit/storage/test_redis_store.py
tests/integration/storage/test_redis_integration.py
```

### **3.2 VectorStore**

#### Test Coverage:

**Vector Operations:**

- ✅ `add_memory()` with embedding generation
- ✅ `get_similar_memories()` semantic search accuracy
- ✅ `get_memories()` retrieval completeness
- ✅ `delete_memory()` by ID
- ✅ `update_memory()` with re-embedding
- ✅ `clear_memories()` complete removal
- ✅ `get_memory_count()` accuracy

**Database Support:**

- ✅ Chroma database integration
- ✅ Pinecone integration (if configured)
- ✅ Vertex AI integration (if configured)
- ✅ Embedding generation and storage
- ✅ Vector similarity calculations
- ✅ Index management

**Search Functionality:**

- ✅ Semantic search accuracy
- ✅ Relevance scoring
- ✅ Search result ranking
- ✅ Query processing
- ✅ Search performance

#### Test Files:

```
tests/unit/storage/test_vector_store.py
tests/integration/storage/test_vector_integration.py
tests/unit/storage/test_embeddings.py
```

### **3.3 Memory Scoring**

#### Test Coverage:

**GeminiScorer:**

- ✅ `score_memory()` therapeutic value assessment
- ✅ Component extraction from complex messages
- ✅ Memory type classification accuracy
- ✅ Storage recommendation generation
- ✅ Significance scoring (relevance, stability, explicitness)
- ✅ Scoring consistency and reliability
- ✅ Edge case handling (empty content, very long content)

#### Test Files:

```
tests/unit/services/test_gemini_scorer.py
tests/unit/services/test_memory_scoring.py
```

---

## 📋 **4. Voice Integration Testing**

### **4.1 Voice Utilities (`utils/voice.py`)**

#### Test Coverage:

**Call Mapping:**

- ✅ `store_call_mapping()` with TTL and metadata
- ✅ `get_customer_id()` retrieval accuracy
- ✅ `get_call_mapping()` full data retrieval
- ✅ `delete_call_mapping()` cleanup
- ✅ TTL expiration handling
- ✅ Mapping data integrity

**Event Processing:**

- ✅ `extract_call_id_from_vapi_event()` from various event formats
- ✅ `is_conversation_update_event()` event type detection
- ✅ `extract_user_message_from_event()` message extraction
- ✅ Event data validation
- ✅ Error handling for malformed events

**Context Management:**

- ✅ `store_conversation_context()` with TTL
- ✅ `get_conversation_context()` retrieval
- ✅ Context data integrity
- ✅ Context expiration handling

#### Test Files:

```
tests/unit/utils/test_voice_utils.py
tests/integration/utils/test_voice_integration.py
```

### **4.2 Voice Service**

#### Test Coverage:

**Webhook Handling:**

- ✅ Vapi webhook signature verification
- ✅ Event type routing (call-start, call-end, analysis-complete)
- ✅ Call record management
- ✅ Error handling and logging
- ✅ Webhook event storage for audit

**Call Management:**

- ✅ Outbound call creation
- ✅ Call status tracking
- ✅ Cost tracking and breakdown
- ✅ Call summary generation
- ✅ Call lifecycle management

**Database Operations:**

- ✅ Voice user management
- ✅ Call record CRUD operations
- ✅ Schedule management
- ✅ Summary storage and retrieval

#### Test Files:

```
tests/unit/services/test_voice_service.py
tests/integration/services/test_voice_integration.py
tests/unit/services/test_webhook_handler.py
```

---

## 📋 **5. Configuration & Environment Testing**

### **5.1 Config Validation**

#### Test Coverage:

**Required Variables:**

- ✅ `GOOGLE_API_KEY` presence and validity
- ✅ Vector database configuration validation
- ✅ Redis URL validation and connectivity
- ✅ Missing variable error handling

**Optional Variables:**

- ✅ Prompt file loading and fallback
- ✅ Environment-specific settings
- ✅ Default value application
- ✅ Configuration override handling

**Prompt Management:**

- ✅ Mental health system prompt loading
- ✅ Conversation guidelines loading
- ✅ Crisis detection prompt loading
- ✅ Memory scoring prompt loading
- ✅ File not found error handling
- ✅ Fallback prompt usage

#### Test Files:

```
tests/unit/config/test_config_validation.py
tests/unit/config/test_prompt_loading.py
tests/integration/config/test_config_integration.py
```

---

## 📋 **6. Security & Privacy Testing**

### **6.1 Authentication & Authorization**

#### Test Coverage:

- ✅ User ID validation in all endpoints
- ✅ Data isolation between users
- ✅ Memory access control
- ✅ Unauthorized access prevention
- ✅ Input validation and sanitization

### **6.2 Data Privacy**

#### Test Coverage:

- ✅ PII detection accuracy across different content types
- ✅ Anonymization effectiveness and irreversibility
- ✅ Consent tracking and application
- ✅ Data retention policy enforcement
- ✅ Audit logging for privacy actions
- ✅ GDPR compliance features
- ✅ Data export functionality

#### Test Files:

```
tests/unit/security/test_authentication.py
tests/unit/security/test_data_privacy.py
tests/unit/security/test_audit_logging.py
tests/integration/security/test_privacy_integration.py
```

---

## 📋 **7. Integration Testing**

### **7.1 End-to-End Workflows**

#### Test Coverage:

**Complete Chat Flow:**

- ✅ User message → Memory processing → Assistant response → Memory storage
- ✅ PII detection → Consent request → User choice → Storage application
- ✅ Crisis detection → Resource provision → Safety protocol
- ✅ Memory context → Personalized response → Context update

**Voice Integration Flow:**

- ✅ Call mapping → Webhook processing → Memory integration → Response generation
- ✅ Voice event → Customer identification → Memory context → Assistant response
- ✅ Call lifecycle → Summary generation → Storage

**Privacy Management Flow:**

- ✅ Memory review → PII detection → User choices → Privacy application
- ✅ Consent management → Choice application → Audit logging
- ✅ Data export → Privacy compliance → User control

#### Test Files:

```
tests/integration/workflows/test_chat_workflow.py
tests/integration/workflows/test_voice_workflow.py
tests/integration/workflows/test_privacy_workflow.py
```

### **7.2 Cross-Service Integration**

#### Test Coverage:

- ✅ Memory service ↔ Chat assistant integration
- ✅ Voice service ↔ Memory service integration
- ✅ Privacy service ↔ Memory service integration
- ✅ Redis ↔ Vector database coordination
- ✅ Service dependency management
- ✅ Error propagation and handling

#### Test Files:

```
tests/integration/cross_service/test_memory_chat_integration.py
tests/integration/cross_service/test_voice_memory_integration.py
tests/integration/cross_service/test_privacy_memory_integration.py
```

---

## 📋 **8. Error Handling & Edge Cases**

### **8.1 Error Scenarios**

#### Test Coverage:

- ✅ Database connection failures
- ✅ API key missing/invalid scenarios
- ✅ Malformed request data handling
- ✅ Memory not found scenarios
- ✅ PII detection service failures
- ✅ Configuration error handling
- ✅ External service timeouts
- ✅ Rate limiting scenarios

### **8.2 Edge Cases**

#### Test Coverage:

- ✅ Empty memory content
- ✅ Very long memory content (>token limits)
- ✅ Special characters and encoding issues
- ✅ Concurrent user operations
- ✅ Memory storage limits
- ✅ TTL expiration edge cases
- ✅ Malformed webhook data
- ✅ Network interruption scenarios

#### Test Files:

```
tests/unit/edge_cases/test_error_handling.py
tests/unit/edge_cases/test_edge_cases.py
tests/integration/edge_cases/test_failure_scenarios.py
```

---

## 📋 **9. Performance Testing**

### **9.1 Load Testing**

#### Test Coverage:

- ✅ Multiple concurrent users
- ✅ Large memory datasets
- ✅ Vector search performance under load
- ✅ Redis memory usage optimization
- ✅ API response time benchmarks
- ✅ Database query performance
- ✅ Memory processing throughput

### **9.2 Scalability Testing**

#### Test Coverage:

- ✅ Memory growth over time
- ✅ Search performance with large datasets
- ✅ Storage efficiency optimization
- ✅ Cache hit rate optimization
- ✅ Resource utilization monitoring
- ✅ Bottleneck identification

#### Test Files:

```
tests/performance/test_load_testing.py
tests/performance/test_scalability.py
tests/performance/test_benchmarks.py
```

---

## 📋 **10. Test Data & Fixtures**

### **10.1 Test Data Management**

#### Coverage:

- ✅ Sample memory content with various PII types
- ✅ Crisis scenario test cases
- ✅ Voice webhook event samples
- ✅ User conversation histories
- ✅ Configuration test scenarios
- ✅ Error condition test data

### **10.2 Test Fixtures**

#### Coverage:

- ✅ Mock external API responses
- ✅ Database state fixtures
- ✅ User account fixtures
- ✅ Memory content fixtures
- ✅ Configuration fixtures

#### Test Files:

```
tests/fixtures/memory_fixtures.py
tests/fixtures/user_fixtures.py
tests/fixtures/voice_fixtures.py
tests/fixtures/config_fixtures.py
```

---

## 📋 **11. Test Execution Strategy**

### **11.1 Test Categories**

1. **Unit Tests** - Fast, isolated component tests
2. **Integration Tests** - Service interaction tests
3. **End-to-End Tests** - Complete workflow tests
4. **Performance Tests** - Load and scalability tests
5. **Security Tests** - Privacy and security validation

### **11.2 Test Environment Setup**

- ✅ Test database isolation
- ✅ Mock external services
- ✅ Test configuration management
- ✅ Cleanup procedures
- ✅ Parallel test execution

### **11.3 Continuous Integration**

- ✅ Automated test execution
- ✅ Test coverage reporting
- ✅ Performance regression detection
- ✅ Security vulnerability scanning
- ✅ Test result reporting

---

## 📋 **12. Test Coverage Goals**

### **Coverage Targets:**

- **Unit Tests:** 90%+ code coverage
- **Integration Tests:** 100% critical path coverage
- **API Tests:** 100% endpoint coverage
- **Security Tests:** 100% privacy feature coverage
- **Performance Tests:** All critical operations benchmarked

### **Quality Gates:**

- All tests must pass before deployment
- No critical security vulnerabilities
- Performance benchmarks must be met
- Code coverage thresholds must be maintained

---

This comprehensive test plan ensures that every aspect of the Nura backend is thoroughly tested, from individual functions to complete user workflows, providing confidence in the system's reliability, security, and performance for mental health applications.
