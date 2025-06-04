# Final Normalized Database Architecture

## 🎯 **Overview**

Successfully eliminated user data duplication by centralizing all user management in a single normalized system.

## 📊 **Database Tables**

### **🔵 Core User System** (`backend/services/user/normalized_models.py`)

- **`users`** - Central user table (Supabase Auth UUID as primary key)

  - id, email, phone_number, full_name, display_name, bio, avatar_url
  - email_confirmed_at, phone_confirmed_at, last_sign_in_at
  - is_active, current_streak, xp, privacy_settings
  - created_at, updated_at, last_active_at, deleted_at

- **`user_service_profiles`** - Service-specific user metadata

  - id, user_id (FK→users.id), service_type, service_preferences
  - service_metadata, usage_stats, created_at, updated_at, last_used_at

- **`user_sync_logs`** - Supabase Auth sync tracking

  - id, user_id (FK→users.id), sync_type, source, before_data, after_data
  - success, error_message, request_id, session_id, created_at

- **`user_sessions`** - Active session management

  - id, user_id (FK→users.id), session_token, service_type, ip_address
  - user_agent, device_info, is_active, expires_at, created_at, last_activity_at, ended_at

- **`user_privacy_settings`** - Privacy preferences and consent
  - id, user_id (FK→users.id), data_retention_days, allow_long_term_storage
  - auto_anonymize_pii, pii_handling_preferences, consent_version, consent_date
  - created_at, updated_at

### **💬 Chat Service** (`backend/services/chat/models.py`)

- **`conversations`** - Chat sessions

  - id, user_id (FK→users.id), title, description, session_type, status
  - crisis_level, safety_plan_triggered, message_count, total_duration_minutes
  - created_at, updated_at, last_message_at

- **`messages`** - Individual chat messages

  - id, conversation_id (FK→conversations.id), user_id (FK→users.id)
  - content, role, message_type, processed_content, pii_detected
  - sentiment_score, crisis_indicators, requires_intervention
  - memory_extracted, memory_items_created, response_time_ms, model_used, tokens_used
  - created_at, updated_at

- **`memory_items`** - Extracted memories from conversations

  - id, user_id (FK→users.id), conversation_id (FK→conversations.id), message_id (FK→messages.id)
  - content, processed_content, memory_type, storage_type, significance_level
  - significance_category, relevance_score, stability_score, explicitness_score, composite_score
  - embedding, pii_detected, user_consent, anonymized_version
  - extraction_metadata, tags, created_at, updated_at, last_accessed_at
  - is_active, is_archived

- **`conversation_summaries`** - Conversation summaries

  - id, conversation_id (FK→conversations.id), user_id (FK→users.id)
  - summary, key_topics, emotional_themes, action_items
  - sentiment_overall, crisis_indicators, therapeutic_progress, summary_metadata
  - created_at, updated_at

- **`system_events`** - Audit log
  - id, user_id (FK→users.id), event_type, event_category
  - event_data, severity, session_id, ip_address, user_agent, created_at

### **🎤 Voice Service** (`backend/services/voice/models.py`)

- **`voices`** - Available voice assistants

  - id, name, assistant_id, description, sample_url, is_active, created_at

- **`voice_calls`** - Voice call records

  - id, vapi_call_id, user_id (FK→users.id), assistant_id (FK→voices.assistant_id)
  - channel, status, phone_number, started_at, ended_at, created_at
  - cost_total, cost_breakdown

- **`voice_schedules`** - Scheduled voice calls

  - id, user_id (FK→users.id), assistant_id (FK→voices.assistant_id)
  - name, cron_expression, timezone, next_run_at, last_run_at
  - is_active, created_at, updated_at, custom_metadata

- **`call_summaries`** - Voice call summaries (NO transcripts)

  - id, call_id (FK→voice_calls.id), user_id (FK→users.id)
  - summary_json, duration_seconds, sentiment, key_topics, action_items
  - crisis_indicators, emotional_state, created_at

- **`webhook_events`** - Vapi webhook log
  - id, vapi_call_id, event_type, payload, processed_at
  - processing_status, error_message

### **📅 Scheduling Service** (`backend/services/scheduling/models.py`)

- **`schedules`** - Unified scheduling for chat/voice checkups

  - id, user_id (FK→users.id), name, description, schedule_type
  - cron_expression, timezone, next_run_at, last_run_at
  - reminder_method, phone_number, email, assistant_id
  - is_active, created_at, updated_at, custom_metadata, context_summary

- **`schedule_executions`** - Schedule execution log
  - id, schedule_id (FK→schedules.id), executed_at, status, error_message
  - user_responded, response_time_minutes, session_duration_minutes, execution_metadata

### **🛡️ Safety Network Service** (`backend/services/safety_network/models.py`)

- **`safety_contacts`** - Emergency contacts

  - id, user_id (FK→users.id), contact_user_id (FK→users.id)
  - external_first_name, external_last_name, external_phone_number, external_email
  - priority_order, allowed_communication_methods, preferred_communication_method
  - relationship_type, notes, preferred_contact_time, timezone
  - is_active, is_emergency_contact, created_at, updated_at
  - last_contacted_at, last_contact_method, last_contact_successful, custom_metadata

- **`contact_logs`** - Contact attempt tracking
  - id, safety_contact_id (FK→safety_contacts.id), user_id (FK→users.id)
  - attempted_at, contact_method, success, reason, initiated_by
  - response_received, response_time_minutes, response_summary
  - message_content, error_message, contact_metadata

## 🔗 **Key Integration Points**

### **✅ Eliminated Duplications**

- ❌ **Removed**: `chat_users`, `voice_users`, `custom_users` tables
- ❌ **Removed**: Duplicate `UserPrivacySettings` in chat service
- ❌ **Removed**: Scattered user data across services
- ✅ **Centralized**: All user data in single `users` table

### **🔄 User Data Flow**

1. **Frontend** → Supabase Auth (handles authentication)
2. **Supabase Auth** → **User Sync Service** (syncs to backend)
3. **Backend Services** → **Normalized Users Table** (single source of truth)
4. **Service-Specific Data** → **user_service_profiles** (preferences only)

### **🔒 Privacy System**

- **Global Settings**: `user_privacy_settings` table
- **Per-Memory Consent**: `memory_items.user_consent` field
- **PII Processing**: Handled by privacy processors with user preferences

### **📊 Data Relationships**

- **All services** reference `users.id` as foreign key
- **No service** duplicates core user information
- **Service profiles** store only service-specific preferences
- **Memory system** integrated with chat service (no separate tables)

## 🚀 **Migration Status**

- ✅ User normalization complete
- ✅ Chat service updated to use normalized users
- ✅ Voice service updated to use normalized users
- ✅ Scheduling service foreign keys added
- ✅ Safety network foreign keys added
- ✅ Privacy settings consolidated
- ✅ Integration services created (ChatUserIntegration, VoiceUserIntegration)

## 🎯 **Result**

**Before**: 4+ scattered user tables with duplicated data
**After**: 1 normalized user system with proper service separation

All user data is now consistently managed, eliminating sync issues and data inconsistencies! 🎉
