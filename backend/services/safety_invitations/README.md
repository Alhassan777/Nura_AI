# Safety Network Invitations System

A comprehensive friend request system for Nura's safety network, enabling users to invite other Nura users to join their safety network through search and invitation functionality.

## 🎯 System Overview

This system implements **one-way safety network invitations** where:

- **Alice** (requester) wants help from **Bob** (requested user)
- Alice searches for Bob by email/name and sends an invitation
- Bob receives the invitation and can accept/decline with custom permissions
- If accepted, Bob becomes Alice's safety contact for crisis intervention and wellness checks

## 🏗️ Architecture

### Database Design (Request-Response Model)

```sql
-- Invitation requests (Alice's request to Bob)
CREATE TABLE safety_network_requests (
    id UUID PRIMARY KEY,
    requester_id UUID REFERENCES users(id),
    requested_user_id UUID REFERENCES users(id),
    status VARCHAR CHECK (status IN ('pending', 'accepted', 'declined', 'cancelled', 'expired')),
    relationship_type VARCHAR,
    invitation_message TEXT,
    requested_permissions JSONB,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Invitation responses (Bob's response to Alice)
CREATE TABLE safety_network_responses (
    id UUID PRIMARY KEY,
    request_id UUID REFERENCES safety_network_requests(id),
    responding_user_id UUID REFERENCES users(id),
    response_type VARCHAR CHECK (response_type IN ('accept', 'decline')),
    response_message TEXT,
    granted_permissions JSONB,
    created_at TIMESTAMP
);
```

## 🚀 Quick Start

### 1. Database Setup

```bash
# Run centralized database initialization (creates ALL Nura tables)
cd backend
python create_tables.py
```

### 2. API Integration

The safety invitations API is automatically integrated when the backend starts:

- **Base URL**: `/safety-invitations`
- **Authentication**: JWT required for all endpoints
- **Documentation**: Available at `/docs` when backend is running

### 3. Start Using the API

```bash
cd backend
python main.py
# API available at: http://localhost:8000/safety-invitations/*
```

## 📡 API Endpoints

### User Search & Discovery

```bash
# Search for users to invite
GET /safety-invitations/search/users?query=john@example.com

# Find user by exact email
GET /safety-invitations/search/user-by-email?email=john@example.com
```

### Invitation Management

```bash
# Send invitation
POST /safety-invitations/invite
{
  "requested_user_email": "bob@example.com",
  "relationship_type": "friend",
  "invitation_message": "Would you like to be my safety contact?",
  "requested_permissions": {...},
  "expires_in_days": 30
}

# Get received invitations
GET /safety-invitations/invitations/received

# Get sent invitations
GET /safety-invitations/invitations/sent

# Respond to invitation
POST /safety-invitations/invitations/{invitation_id}/respond
{
  "response_type": "accept",
  "response_message": "Happy to help!",
  "granted_permissions": {...}
}

# Cancel invitation
DELETE /safety-invitations/invitations/{invitation_id}
```

### Templates & Helpers

```bash
# Get permission templates
GET /safety-invitations/templates/default-permissions

# Get relationship types
GET /safety-invitations/relationship-types
```

## 🔐 Security Features

- **JWT Authentication**: All endpoints require valid JWT tokens
- **User Isolation**: Users can only see/manage their own invitations
- **Privacy Protection**: Search results exclude sensitive user information
- **Permission Control**: Granular permission system for granted access
- **Expiration**: Automatic cleanup of expired invitations

## 🔄 Integration with Safety Network

When an invitation is **accepted**:

1. A `SafetyContact` record is created in the main safety network
2. The accepted user becomes a safety contact for the requester
3. Permissions are applied based on the response
4. Both users are notified of the successful connection

## 🗂️ File Structure

```
backend/services/safety_invitations/
├── __init__.py          # Service exports
├── api.py              # FastAPI endpoints
├── manager.py          # Core business logic
├── search.py           # User search functionality
├── database.py         # Database session management
└── README.md           # This documentation
```

## 🛠️ Development

### Database Management

- **No local database setup needed** - uses centralized `backend/create_tables.py`
- **Session management** handled in `database.py`
- **Models defined** in main `backend/models.py`

### Adding Features

1. Add business logic to `manager.py`
2. Add API endpoints to `api.py`
3. Update search functionality in `search.py`
4. All database changes go in main `models.py`

### Testing

```bash
# Run the full backend
cd backend
python main.py

# Test endpoints at http://localhost:8000/docs
```

## 🎮 Usage Flow

1. **Alice searches** for Bob: `GET /search/users?query=bob@example.com`
2. **Alice sends invitation**: `POST /invite` with Bob's email
3. **Bob receives notification** (in-app + email)
4. **Bob views invitation**: `GET /invitations/received`
5. **Bob responds**: `POST /invitations/{id}/respond` with accept/decline
6. **Safety contact created** automatically if accepted
7. **Both users notified** of the outcome

## 🔧 Configuration

The service uses the main application's database configuration:

- **Database URL**: From environment variable `DATABASE_URL`
- **Session management**: Automatic cleanup and error handling
- **Connection pooling**: Optimized for concurrent requests

## 📊 Permission System

### Default Templates

- **Emergency Only**: Crisis intervention, emergency contact
- **Wellness Support**: Full support including check-ins
- **Basic Support**: Limited to wellness check-ins
- **Family Member**: Full access for close family

### Custom Permissions

Users can create custom permission sets when responding to invitations:

```json
{
  "emergency_contact": true,
  "wellness_checks": true,
  "crisis_intervention": true,
  "communication_methods": ["phone", "sms", "email"],
  "time_restrictions": "business_hours"
}
```

## 🚀 Ready to Use!

The safety invitations system is now fully integrated and ready for production use! All database setup is handled centrally, and the API is automatically available when the Nura backend starts.
