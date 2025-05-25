# Nura Memory & Context Service

A service for managing short-term and long-term memories in the Nura application, with support for PII detection, consent management, and audit logging.

## Features

- **Short-term Coherence**: Maintains recent context using Redis for fast access
- **Long-term Personalization**: Stores important memories in Chroma/Vertex AI for semantic search
- **Sensitive Data Detection**: Uses Presidio + Hugging Face for PII detection
- **Memory Management**: Endpoints for creating, retrieving, and deleting memories
- **Audit Compliance**: Comprehensive logging of all memory operations

## Architecture

The service uses a two-tier memory system:

- **Short-term Memory**: Redis for fast access to recent context
- **Long-term Memory**: Chroma/Vertex AI for semantic search and persistence

Memory scoring is performed using Gemini, which evaluates:

- Relevance to current context
- Stability of information
- Explicit user intent
- Sensitivity of content

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
# Required
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_API_KEY=your-api-key

# Optional
export REDIS_URL=redis://localhost:6379
export CHROMA_PERSIST_DIR=./chroma
export USE_VERTEX_AI=false
```

3. Run the service:

```bash
# Development
python -m src.services.memory.main

# Production
docker-compose up
```

## API Endpoints

### Memory Operations

- `POST /chat?user_id=<user_id>`: Process a new chat message
- `POST /memory/context?user_id=<user_id>`: Get memory context for a user
- `GET /memory/stats?user_id=<user_id>`: Get memory statistics
- `DELETE /memory/{memory_id}?user_id=<user_id>`: Delete a specific memory
- `POST /memory/forget?user_id=<user_id>`: Clear all memories
- `POST /memory/consent?user_id=<user_id>`: Handle consent for sensitive memories
- `POST /memory/export?user_id=<user_id>`: Export all memories

### Authentication

**Note**: JWT authentication is currently not implemented. The service uses query parameters to identify users:

```
GET /memory/stats?user_id=demo-user-123
```

For production use, you may want to implement proper authentication.

## Memory Scoring

Memories are scored based on:

1. **Relevance**: How directly it relates to the current context
2. **Stability**: How likely it is to remain true/valid
3. **Explicitness**: How explicitly the user intended to store it
4. **Sensitivity**: Whether it contains sensitive information

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black src/
isort src/
flake8 src/
```

## Security

- PII detection and anonymization
- Explicit consent for sensitive data
- Audit logging of all operations
- (JWT authentication - planned for future implementation)

## Monitoring

The service exposes metrics for Prometheus:

- Memory counts by type
- PII detection events
- Consent management events
- API request latency

## License

MIT License
