# Vapi Integration Guide

This document explains how the Vapi.ai voice assistant has been integrated into the Nura frontend application.

## Overview

The Vapi integration enables real-time voice conversations with the Nura AI assistant through the web browser. The integration consists of several key components:

## Key Components

### 1. Voice API Service (`/src/services/apis/voice.ts`)

- Handles backend API calls for voice functionality
- Manages browser call initialization
- Provides call status, history, and summary endpoints

### 2. Vapi Hook (`/src/hooks/useVapi.ts`)

- Custom React hook that manages Vapi state and interactions
- Handles call lifecycle (start, end, mute, etc.)
- Manages event listeners for transcripts, speech detection, and errors
- Provides real-time audio level monitoring

### 3. VoiceChat Component (`/src/components/voice/VoiceChat.tsx`)

- Main UI component for voice conversations
- Shows call status, audio visualization, and controls
- Displays real-time transcripts and conversation history
- Provides mute/unmute and call end/start functionality

### 4. Voice Chat Page (`/src/app/voice-chat/page.tsx`)

- Full page implementation with call options
- Integration point that passes assistant ID to VoiceChat component

## Environment Variables

The following environment variables are required in `.env.local`:

```
# Vapi.ai Configuration
NEXT_PUBLIC_VAPI_PUBLIC_KEY=your_vapi_public_key
NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID=your_assistant_id
```

## Usage Example

```tsx
import { VoiceChat } from "@/components/voice/VoiceChat";

function MyComponent() {
  return (
    <VoiceChat
      assistantId="your-assistant-id"
      onCallStart={() => console.log("Call started")}
      onCallEnd={() => console.log("Call ended")}
      onSwitchToChat={() => {
        /* Navigate to text chat */
      }}
    />
  );
}
```

## Using the Vapi Hook Directly

```tsx
import { useVapi } from "@/hooks/useVapi";

function CustomVoiceComponent() {
  const { state, actions, utils } = useVapi({
    assistantId: "your-assistant-id",
    onMessage: (message) => {
      if (message.type === "transcript") {
        console.log("Transcript:", message.transcript);
      }
    },
    onError: (error) => {
      console.error("Voice error:", error);
    },
  });

  return (
    <div>
      <button onClick={actions.startCall} disabled={!state.isConnected}>
        {state.isCallActive ? "End Call" : "Start Call"}
      </button>

      {state.isCallActive && (
        <p>Call Duration: {utils.formatDuration(state.callDuration)}</p>
      )}
    </div>
  );
}
```

## Features

### Real-time Voice Conversation

- Browser-based voice calls using WebRTC
- Automatic speech recognition and synthesis
- Real-time audio level monitoring

### Call Management

- Start/end voice calls
- Mute/unmute functionality
- Call duration tracking
- Connection status monitoring

### Transcript & History

- Real-time conversation transcripts
- Speaker identification (User vs Nura)
- Conversation history display

### Error Handling

- Connection error management
- Graceful fallback to text chat
- User-friendly error messages

### Backend Integration

- Secure JWT-based authentication
- Call metadata storage
- Integration with existing user system

## State Management

The `useVapi` hook provides the following state:

```typescript
interface VapiState {
  isConnected: boolean; // Vapi connection status
  isCallActive: boolean; // Whether a call is in progress
  isLoading: boolean; // Loading states
  isMuted: boolean; // Microphone mute status
  isAssistantSpeaking: boolean; // When Nura is speaking
  audioLevel: number; // Real-time audio level (0-100)
  callDuration: number; // Call duration in seconds
  error: string | null; // Error messages
  transcript: string; // Latest transcript
  callId?: string; // Backend call ID
}
```

## Actions Available

```typescript
const actions = {
  initializeVapi: () => void;           // Initialize Vapi connection
  startCall: () => Promise<void>;       // Start voice call
  endCall: () => Promise<void>;         // End voice call
  toggleMute: () => void;               // Toggle microphone mute
  sendMessage: (msg: string) => void;   // Send text message during call
  say: (msg: string) => void;           // Make assistant speak
};
```

## Backend Requirements

The frontend expects the following backend endpoints:

- `POST /voice/calls/browser` - Initialize browser call
- `GET /voice/calls/{id}/status` - Get call status
- `POST /voice/calls/{id}/end` - End call
- `GET /voice/calls` - Get call history

## Dependencies

- `@vapi-ai/web` - Official Vapi Web SDK
- `antd` - UI components
- `lucide-react` - Icons

## Browser Support

- Chrome 60+ (recommended)
- Firefox 60+
- Safari 12+
- Edge 79+

Requires microphone permissions and WebRTC support.

## Troubleshooting

### Common Issues

1. **Microphone Permission Denied**

   - Ensure browser has microphone permissions
   - Check browser security settings

2. **Connection Errors**

   - Verify environment variables are set correctly
   - Check network connectivity
   - Ensure backend voice service is running

3. **No Audio**
   - Check system audio settings
   - Verify browser audio permissions
   - Test with different audio devices

### Debug Information

Enable debug logging by setting `NODE_ENV=development` in your environment. The Vapi hook will log detailed information about:

- Connection status
- Call events
- Message handling
- Error details

## Next Steps

- Add phone call support
- Implement call recording (if needed)
- Add voice commands
- Enhance audio visualization
- Add call analytics
