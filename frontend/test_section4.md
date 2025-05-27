# Section 4: Frontend Glue - Test Guide

## Overview

This document provides comprehensive testing instructions for Section 4 (Frontend Glue) of the Vapi.ai voice integration roadmap.

## Components Implemented

### ✅ **Task 4.1: VoiceCallButton Component**

- **File**: `frontend/components/VoiceCallButton.tsx`
- **Features**:
  - Web call initiation using Vapi Web SDK
  - Phone call triggering via server-side API
  - Real-time call state management
  - Volume visualization during calls
  - Mute/unmute functionality for web calls
  - Error handling and user feedback

### ✅ **Task 4.2: LiveTranscript Component**

- **File**: `frontend/components/LiveTranscript.tsx`
- **Features**:
  - Real-time transcript display
  - Message timestamps and confidence scores
  - Auto-scroll functionality
  - Transcript export (copy/download)
  - Current speaker indicators
  - Collapsible interface

### ✅ **Integration Demo Page**

- **File**: `frontend/app/voice-demo/page.tsx`
- **Features**:
  - Complete voice interface demonstration
  - Both web and phone call modes
  - Live transcript integration
  - Demo controls for testing

## Testing Instructions

### 1. Manual Component Testing

#### Test VoiceCallButton - Web Mode

```bash
# Navigate to the demo page
# http://localhost:3000/voice-demo

# Test Case 1: Web Call Initialization
1. Click on "Web Call" tab
2. Click the microphone button to start call
3. Verify browser prompts for microphone permission
4. Check that button state changes to "connecting" then "active"
5. Confirm volume visualization appears during speech

# Test Case 2: Mute/Unmute Functionality
1. During an active web call
2. Click the mute button (should appear below main button)
3. Verify microphone icon changes and status text updates
4. Click unmute to restore audio

# Test Case 3: Call Termination
1. During an active call
2. Click the main button (now shows disconnect icon)
3. Verify call ends and button returns to initial state
```

#### Test VoiceCallButton - Phone Mode

```bash
# Test Case 4: Phone Call Setup
1. Click on "Phone Call" tab
2. Enter a valid phone number: +1 (555) 123-4567
3. Verify button becomes enabled
4. Click the phone button
5. Check that API call is made to /api/voice/start

# Test Case 5: Phone Number Validation
1. Leave phone number field empty
2. Verify button remains disabled
3. Enter invalid format
4. Test with different valid formats
```

#### Test LiveTranscript Component

```bash
# Test Case 6: Transcript Display
1. Start a voice call (web or phone)
2. Verify initial assistant message appears
3. Use "Add User Message" button to simulate conversation
4. Check message formatting, timestamps, and avatars

# Test Case 7: Transcript Features
1. With multiple messages in transcript:
   - Test copy functionality (copy button)
   - Test download functionality (download button)
   - Verify auto-scroll behavior
   - Test visibility toggle (hide/show transcript)

# Test Case 8: Real-time Updates
1. During active call simulation
2. Add messages alternating between user and assistant
3. Verify current speaker indicator updates
4. Check message confidence scores display
```

### 2. API Integration Testing

#### Test Voice Start API

```bash
# Test Case 9: Web Mode API Call
curl -X GET "http://localhost:3000/api/voice/start?mode=web&customerId=test-user-123"

# Expected Response:
{
  "mode": "web",
  "startPayload": {
    "assistantId": "vapi-assistant-id",
    "customerId": "test-user-123",
    "metadata": { ... }
  },
  "success": true
}

# Test Case 10: Phone Mode API Call
curl -X POST "http://localhost:3000/api/voice/start" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "phone",
    "phoneNumber": "+15551234567",
    "customerId": "test-user-123"
  }'

# Expected Response:
{
  "mode": "phone",
  "callId": "vapi-call-id",
  "status": "queued",
  "success": true
}
```

### 3. Vapi SDK Integration Testing

#### Test Vapi Web SDK Events

```javascript
// Test Case 11: Vapi Event Handling
// Open browser console during web call test
// Verify these events are logged:

// ✅ Call start event
"📞 Call started: { id: 'call-id-123', ... }";

// ✅ Volume level events
"🎙️ User started speaking";
"🎙️ User stopped speaking";

// ✅ Message events
"💬 Message received: { type: 'transcript', transcript: '...', role: 'user' }";

// ✅ Call end event
"📞 Call ended: { id: 'call-id-123', ... }";
```

### 4. Error Handling Testing

#### Test Error Scenarios

```bash
# Test Case 12: Missing Configuration
1. Remove NEXT_PUBLIC_VAPI_WEB_KEY from environment
2. Attempt to start web call
3. Verify error message appears
4. Check console for configuration warnings

# Test Case 13: Network Errors
1. Disconnect internet during call setup
2. Verify timeout handling
3. Check user-friendly error messages
4. Test recovery after network restoration

# Test Case 14: Permission Denied
1. Block microphone access in browser
2. Attempt web call
3. Verify appropriate error handling
4. Check guidance message for user
```

### 5. User Experience Testing

#### Test User Flow

```bash
# Test Case 15: Complete Web Call Flow
1. Navigate to /voice-demo
2. Read introduction and feature highlights
3. Select web call mode
4. Grant microphone permission
5. Start voice call
6. Speak test phrases and observe transcript
7. Use mute/unmute controls
8. End call gracefully
9. Export transcript

# Test Case 16: Complete Phone Call Flow
1. Navigate to /voice-demo
2. Select phone call mode
3. Enter phone number
4. Initiate call
5. Verify status updates
6. Monitor transcript during call
7. End call appropriately
```

### 6. Integration with Backend Testing

#### Test Backend Connection

```bash
# Test Case 17: Call Mapping Storage
1. Start web or phone call
2. Check that call mapping is stored:
   - GET /voice/mapping/{call-id}
   - Verify customerId is correctly mapped

# Test Case 18: Webhook Processing
1. During active call
2. Simulate Vapi webhook events
3. Verify transcript updates in real-time
4. Check backend processing logs

# Test Case 19: Memory Integration
1. Complete a voice conversation
2. Verify messages are stored in memory service
3. Check that conversation context is maintained
4. Test retrieval of conversation history
```

## Expected Results

### ✅ **Performance Targets**

- Call setup time: < 3 seconds
- Transcript update latency: < 500ms
- UI responsiveness: Smooth animations
- Memory usage: Stable during long calls

### ✅ **User Experience Goals**

- Intuitive call controls
- Clear visual feedback
- Accessible error messages
- Seamless mode switching (web/phone)

### ✅ **Integration Validation**

- All API endpoints responding correctly
- Vapi SDK events properly handled
- Backend webhook processing working
- Memory service integration functional

## Troubleshooting

### Common Issues

1. **Microphone Permission Denied**

   - Solution: Check browser settings, use HTTPS
   - Verify: Browser console shows permission status

2. **Vapi SDK Not Loading**

   - Solution: Check NEXT_PUBLIC_VAPI_WEB_KEY configuration
   - Verify: Network tab shows SDK loading successfully

3. **API Calls Failing**

   - Solution: Verify backend is running on correct port
   - Verify: Check /health endpoint responds

4. **Transcript Not Updating**
   - Solution: Check WebSocket connection
   - Verify: Event listeners are properly attached

## Success Criteria

### ✅ **Section 4 Complete When:**

- All test cases pass
- Both web and phone modes functional
- Live transcript displays correctly
- API integration works seamlessly
- Error handling provides good UX
- Zero regression in existing chat features

---

**Status**: Section 4 Implementation Complete ✅  
**Next**: Ready for Section 5 (Crisis Escalation via Voice)
