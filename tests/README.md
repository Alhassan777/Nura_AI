# Nura App Tests

This directory contains all test files organized by component.

## Structure

```
tests/
├── backend/           # Backend API and service tests
├── memory-service/    # Memory service specific tests
└── frontend/          # Frontend component tests (when added)
```

## Backend Tests

- `test_vector_*.py` - Vector database and embedding tests
- `test_voice_*.py` - Voice API and webhook tests
- `test_simple_gemini.py` - Gemini AI integration tests
- `test_optimized_system.py` - Optimized memory system tests
- `test_privacy_system.py` - Privacy and PII detection tests
- `test_sensitive_info_detection.py` - Sensitive information detection tests
- `test_cleaned_endpoints.py` - API endpoint tests

## Memory Service Tests

- `test_api.py` - Memory service API tests
- `test_config.py` - Configuration validation tests
- `test_vector_store.py` - Vector storage tests
- `test_redis_store.py` - Redis storage tests
- `test_audit_logger.py` - Audit logging tests
- `test_pii_detector.py` - PII detection tests
- `test_config_errors.py` - Configuration error handling tests

## Running Tests

### Backend Tests

```bash
cd backend
python -m pytest ../tests/backend/ -v
```

### Memory Service Tests

```bash
cd backend
python -m pytest ../tests/memory-service/ -v
```

### All Tests

```bash
python -m pytest tests/ -v
```

## Environment Setup

Make sure you have your `.env` file configured properly before running tests. See `backend/env.example` for required environment variables.
