# Tests Directory Organization

This directory contains all test files for the Nura application, organized by test type and functionality.

## 📁 Directory Structure

```
tests/
├── unit/                           # Unit tests (fast, isolated component tests)
│   ├── api/                        # API endpoint unit tests
│   │   ├── chat/                   # Chat API tests
│   │   ├── memory/                 # Memory API tests
│   │   ├── privacy/                # Privacy API tests
│   │   └── voice/                  # Voice API tests
│   ├── backend/                    # Backend-specific unit tests
│   ├── config/                     # Configuration tests
│   ├── edge_cases/                 # Edge case handling tests
│   ├── frontend/                   # Frontend unit tests
│   ├── security/                   # Security and authentication tests
│   ├── services/                   # Service layer tests
│   │   ├── crisis/                 # Crisis detection service tests
│   │   ├── image_generation/       # Image generation service tests
│   │   ├── memory/                 # Memory service tests
│   │   ├── privacy/                # Privacy service tests
│   │   └── safety/                 # Safety service tests
│   ├── storage/                    # Storage layer tests (Redis, Vector DB)
│   └── utils/                      # Utility function tests
│
├── integration/                    # Integration tests (service interactions)
│   ├── api/                        # API integration tests
│   ├── backend/                    # Backend integration tests
│   ├── crisis/                     # Crisis intervention workflow tests
│   ├── cross_service/              # Cross-service integration tests
│   ├── external/                   # External API integration tests
│   ├── frontend/                   # Frontend integration tests
│   ├── image_generation/           # Image generation pipeline tests
│   ├── services/                   # Service integration tests
│   ├── storage/                    # Storage integration tests
│   └── workflows/                  # Complete workflow tests
│
├── functional/                     # Functional tests (end-to-end features)
│   ├── chat_test_interface.py      # Interactive chat testing interface
│   ├── crisis/                     # Crisis intervention functional tests
│   ├── image_generation/           # Image generation functional tests
│   ├── memory/                     # Memory management functional tests
│   └── privacy/                    # Privacy management functional tests
│
├── system/                         # System-level tests
│   ├── load/                       # Load testing
│   └── performance/                # Performance testing
│
├── fixtures/                       # Test data and fixtures
├── documentation/                  # Test documentation and plans
│   ├── COMPREHENSIVE_TEST_PLAN.md  # Master test plan
│   ├── SAFETY_INVITATIONS_TEST_REPORT.md
│   └── TESTING_IMPLEMENTATION_ROADMAP.md
│
├── conftest.py                     # Pytest configuration and shared fixtures
└── README.md                       # This file
```

## 🧪 Test Types

### Unit Tests (`unit/`)

- **Purpose**: Test individual components in isolation
- **Characteristics**: Fast, no external dependencies, mocked services
- **Coverage**: Functions, classes, modules
- **Run time**: < 1 second per test

### Integration Tests (`integration/`)

- **Purpose**: Test interactions between components
- **Characteristics**: May use real databases, external services
- **Coverage**: Service interactions, API endpoints, data flow
- **Run time**: 1-10 seconds per test

### Functional Tests (`functional/`)

- **Purpose**: Test complete features from user perspective
- **Characteristics**: End-to-end workflows, real scenarios
- **Coverage**: User stories, business requirements
- **Run time**: 10-60 seconds per test

### System Tests (`system/`)

- **Purpose**: Test system behavior under various conditions
- **Characteristics**: Load testing, performance testing, stress testing
- **Coverage**: System limits, scalability, reliability
- **Run time**: Minutes to hours

## 🏃 Running Tests

### Run All Tests

```bash
# From project root
python -m pytest tests/ -v
```

### Run by Category

```bash
# Unit tests only (fast)
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Functional tests
python -m pytest tests/functional/ -v

# System tests
python -m pytest tests/system/ -v
```

### Run by Feature

```bash
# Image generation tests
python -m pytest tests/unit/services/image_generation/ tests/integration/image_generation/ tests/functional/image_generation/ -v

# Crisis intervention tests
python -m pytest tests/unit/services/crisis/ tests/integration/crisis/ tests/functional/crisis/ -v

# Memory system tests
python -m pytest tests/unit/services/memory/ tests/integration/workflows/ -v

# Privacy system tests
python -m pytest tests/unit/services/privacy/ tests/functional/privacy/ -v
```

### Run Specific Tests

```bash
# Image generation pipeline
python -m pytest tests/integration/image_generation/test_image_generation_pipeline.py -v

# Crisis intervention production test
python -m pytest tests/functional/crisis/test_chat_crisis_intervention_production.py -v

# Privacy retrieval test
python -m pytest tests/functional/privacy/privacy_retrieval_test.py -v
```

## 🎯 Test Coverage Goals

| Test Type       | Coverage Target        | Focus Areas                                      |
| --------------- | ---------------------- | ------------------------------------------------ |
| **Unit**        | 90%+                   | Individual functions, error handling, edge cases |
| **Integration** | 100% critical paths    | Service interactions, API endpoints              |
| **Functional**  | 100% user stories      | Complete workflows, business logic               |
| **System**      | Performance benchmarks | Load limits, scalability, reliability            |

## 📋 Test Organization Principles

### File Naming Convention

- Unit tests: `test_[component_name].py`
- Integration tests: `test_[feature]_integration.py`
- Functional tests: `test_[feature]_functional.py`
- System tests: `test_[aspect]_system.py`

### Directory Mapping

Tests are organized to mirror the main application structure:

```
backend/services/memory/           → tests/unit/services/memory/
backend/services/image_generation/ → tests/unit/services/image_generation/
backend/api/memory/               → tests/unit/api/memory/
nura-fe/components/               → tests/unit/frontend/
```

### Test Dependencies

- **Unit tests**: No external dependencies (mocked)
- **Integration tests**: Local services (Redis, ChromaDB)
- **Functional tests**: Full environment (Supabase, external APIs)
- **System tests**: Production-like environment

## 🛠️ Development Workflow

### Adding New Tests

1. Identify the appropriate test type and directory
2. Follow the naming convention
3. Use existing fixtures from `conftest.py`
4. Update this README if adding new categories

### Test-Driven Development

1. Write failing test first (`tests/unit/`)
2. Implement minimal code to pass
3. Add integration tests (`tests/integration/`)
4. Add functional tests (`tests/functional/`)
5. Refactor with confidence

### Pre-commit Testing

```bash
# Quick unit tests (< 30 seconds)
python -m pytest tests/unit/ -x --tb=short

# Critical integration tests (< 2 minutes)
python -m pytest tests/integration/api/ tests/integration/services/ -x
```

## 📊 Test Metrics

### Performance Benchmarks

- **Unit tests**: All tests < 30 seconds total
- **Integration tests**: All tests < 5 minutes total
- **Functional tests**: All tests < 15 minutes total
- **System tests**: Varies by scope

### Quality Gates

- All tests must pass before merge
- Coverage thresholds must be maintained
- Performance benchmarks must be met
- No critical security vulnerabilities

## 🔧 Configuration

### Test Environment Setup

Tests use configuration from:

1. `conftest.py` - Shared fixtures and setup
2. `pytest.ini` - Pytest configuration
3. `.env.test` - Test environment variables
4. `fixtures/` - Test data and mock responses

### Test Database

- Unit tests: In-memory/mocked
- Integration tests: Test Redis/ChromaDB instances
- Functional tests: Test Supabase project
- System tests: Production-like setup

## 📚 Documentation

- **Test Plans**: `tests/documentation/`
- **Test Reports**: Generated in `tests/reports/`
- **Coverage Reports**: `tests/coverage/`
- **Performance Reports**: `tests/performance/reports/`

## 🤝 Contributing

When adding new tests:

1. Follow the directory structure
2. Use appropriate test type
3. Include docstrings explaining test purpose
4. Add fixtures for reusable test data
5. Update documentation if needed

This organization ensures tests are easy to find, run, and maintain while providing comprehensive coverage of the Nura application.
