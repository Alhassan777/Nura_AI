# Frontend API Quick Reference Guide

Quick reference for connecting the Nura frontend to backend API endpoints.

## 🔗 Backend API Endpoints Overview

### Base Configuration

```typescript
// Environment Variables (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### API Client Setup

```typescript
// src/services/apis/index.ts
import axios from "axios";

export const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL, // http://localhost:8000
});

// Auto-attach auth token
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem("supabase.auth.token"); // Or from Supabase
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

## 📋 Available Backend Services

### 1. Authentication (`/auth`)

```typescript
// Login
POST /auth/login
Body: { email: string, password: string }

// Register
POST /auth/register
Body: { email: string, password: string, full_name?: string }

// Logout
POST /auth/logout

// Refresh token
POST /auth/refresh
Body: { refresh_token: string }

// Frontend Implementation
export const authApi = {
  login: (credentials: { email: string; password: string }) =>
    axiosInstance.post('/auth/login', credentials),

  register: (userData: { email: string; password: string; full_name?: string }) =>
    axiosInstance.post('/auth/register', userData),

  logout: () => axiosInstance.post('/auth/logout'),
};
```

### 2. Chat Service (`/chat`)

**Note**: Enhanced with refactored mental health assistant featuring modular extractors and improved capabilities.

```typescript
// Send message (Enhanced with modular assistant)
POST /chat
Body: {
  message?: string;
  include_memory?: boolean;
  endpoint?: string;
  method?: string;
  body?: any;
}

// Response includes enhanced analysis from refactored assistant:
Response: {
  response: string;
  crisis_level: "CRISIS" | "CONCERN" | "SUPPORT";
  crisis_explanation: string;
  schedule_analysis: {
    should_suggest_scheduling: boolean;
    extracted_schedule?: object;
    schedule_opportunity_type?: string;
  };
  action_plan_analysis: {
    should_suggest_action_plan: boolean;
    action_plan_type?: "therapeutic_emotional" | "personal_achievement";
    extracted_action_plan?: object;
  };
  session_metadata: object;
  resources_provided: string[];
  coping_strategies: string[];
  timestamp: string;
  crisis_flag: boolean;
  configuration_warning: boolean;
}

// Get chat history
GET /chat/history?limit=50&offset=0

// Clear chat history
DELETE /chat/history

// Frontend Implementation
export const chatApi = {
  sendMessage: (payload: {
    message?: string;
    include_memory?: boolean;
  }) => axiosInstance.post('/chat', payload),

  getChatHistory: (limit = 50, offset = 0) =>
    axiosInstance.get(`/chat/history?limit=${limit}&offset=${offset}`),

  clearHistory: () => axiosInstance.delete('/chat/history'),
};

// React Hook
export const useSendMessage = () => {
  return useMutation({
    mutationFn: chatApi.sendMessage,
    onSuccess: () => {
      // Invalidate chat history
      queryClient.invalidateQueries(['chat', 'history']);
    },
  });
};
```

### 3. Mental Health Assistant (`/assistant`)

**New**: Direct access to the refactored modular mental health assistant.

```typescript
// Process message with full assistant capabilities
POST /assistant/process
Body: {
  user_id: string;
  message: string;
  conversation_context?: object;
}

// Get crisis resources
GET /assistant/crisis-resources

// Frontend Implementation
export const assistantApi = {
  processMessage: (data: {
    user_id: string;
    message: string;
    conversation_context?: object;
  }) => axiosInstance.post('/assistant/process', data),

  getCrisisResources: () => axiosInstance.get('/assistant/crisis-resources'),
};

// React Hooks
export const useProcessMessage = () => {
  return useMutation({
    mutationFn: assistantApi.processMessage,
    onSuccess: (data) => {
      // Handle crisis flags
      if (data.crisis_flag) {
        // Trigger crisis intervention UI
        console.warn('Crisis detected:', data.crisis_explanation);
      }
    },
  });
};
```

### 4. Memory Service (`/memory`)

```typescript
// Get privacy review
GET /memory/privacy-review/{userId}

// Apply privacy choices
POST /memory/apply-privacy-choices/{userId}
Body: { choices: PrivacyChoices }

// Get memory statistics
GET /memory/stats/{userId}

// Search memories
GET /memory/search?query=string&limit=10

// Push memory (from Vapi)
POST /memory/push
Body: { memory: string, type: 'short_term' | 'long_term' | 'emotional_anchor' }

// Frontend Implementation
export const memoryApi = {
  getPrivacyReview: (userId: string) =>
    axiosInstance.get(`/memory/privacy-review/${userId}`),

  applyPrivacyChoices: (userId: string, choices: any) =>
    axiosInstance.post(`/memory/apply-privacy-choices/${userId}`, choices),

  getMemoryStats: (userId: string) =>
    axiosInstance.get(`/memory/stats/${userId}`),

  searchMemories: (query: string, limit = 10) =>
    axiosInstance.get(`/memory/search?query=${query}&limit=${limit}`),
};
```

### 5. User Management (`/users`)

```typescript
// Get user profile
GET /users/profile

// Update user profile
PUT /users/profile
Body: { full_name?: string, preferences?: object }

// Get user settings
GET /users/settings

// Update user settings
PUT /users/settings
Body: { theme?: string, notifications?: boolean }

// Frontend Implementation
export const userApi = {
  getProfile: () => axiosInstance.get('/users/profile'),

  updateProfile: (data: { full_name?: string; preferences?: object }) =>
    axiosInstance.put('/users/profile', data),

  getSettings: () => axiosInstance.get('/users/settings'),

  updateSettings: (settings: { theme?: string; notifications?: boolean }) =>
    axiosInstance.put('/users/settings', settings),
};

// React Hooks
export const useUserProfile = () => {
  return useQuery({
    queryKey: ['user', 'profile'],
    queryFn: userApi.getProfile,
  });
};

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: userApi.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries(['user', 'profile']);
    },
  });
};
```

### 6. Gamification (`/gamification`)

```typescript
// Get user badges
GET /gamification/badges

// Get user stats
GET /gamification/stats

// Get leaderboard
GET /gamification/leaderboard?limit=10

// Award badge (admin)
POST /gamification/badges/award
Body: { user_id: string, badge_id: string }

// Frontend Implementation
export const gamificationApi = {
  getBadges: () => axiosInstance.get('/gamification/badges'),

  getStats: () => axiosInstance.get('/gamification/stats'),

  getLeaderboard: (limit = 10) =>
    axiosInstance.get(`/gamification/leaderboard?limit=${limit}`),
};

// React Hooks
export const useUserBadges = () => {
  return useQuery({
    queryKey: ['gamification', 'badges'],
    queryFn: gamificationApi.getBadges,
  });
};

export const useUserStats = () => {
  return useQuery({
    queryKey: ['gamification', 'stats'],
    queryFn: gamificationApi.getStats,
  });
};
```

### 7. Safety Network (`/safety_network`)

```typescript
// Get safety network
GET /safety_network

// Add contact
POST /safety_network/contacts
Body: { contact_id: string, relationship_type: string }

// Remove contact
DELETE /safety_network/contacts/{contact_id}

// Get emergency contacts
GET /safety_network/emergency-contacts

// Update emergency contact status
PUT /safety_network/emergency-contacts/{contact_id}
Body: { is_emergency_contact: boolean }

// Frontend Implementation
export const safetyNetworkApi = {
  getNetwork: () => axiosInstance.get('/safety_network'),

  addContact: (data: { contact_id: string; relationship_type: string }) =>
    axiosInstance.post('/safety_network/contacts', data),

  removeContact: (contactId: string) =>
    axiosInstance.delete(`/safety_network/contacts/${contactId}`),

  getEmergencyContacts: () =>
    axiosInstance.get('/safety_network/emergency-contacts'),
};
```

### 8. Safety Invitations (`/safety-invitations`)

```typescript
// Search users
POST /safety-invitations/search/users
Body: { query: string, limit: number }

// Send invitation
POST /safety-invitations/invite
Body: {
  recipient_email: string;
  relationship_type: string;
  requested_permissions: object;
  invitation_message?: string;
}

// Get pending invitations
GET /safety-invitations/pending

// Accept invitation
POST /safety-invitations/{invitation_id}/accept
Body: { granted_permissions: object }

// Reject invitation
POST /safety-invitations/{invitation_id}/reject

// Frontend Implementation
export const safetyInvitationsApi = {
  searchUsers: (query: string, limit = 10) =>
    axiosInstance.post('/safety-invitations/search/users', { query, limit }),

  sendInvitation: (data: {
    recipient_email: string;
    relationship_type: string;
    requested_permissions: object;
    invitation_message?: string;
  }) => axiosInstance.post('/safety-invitations/invite', data),

  getPendingInvitations: () =>
    axiosInstance.get('/safety-invitations/pending'),

  acceptInvitation: (invitationId: string, permissions: object) =>
    axiosInstance.post(`/safety-invitations/${invitationId}/accept`, {
      granted_permissions: permissions,
    }),
};
```

### 9. Voice Service (`/voice`)

```typescript
// Get voice settings
GET /voice/settings

// Update voice settings
PUT /voice/settings
Body: { voice_id?: string, speed?: number, pitch?: number }

// Get available voices
GET /voice/available-voices

// Frontend Implementation
export const voiceApi = {
  getSettings: () => axiosInstance.get('/voice/settings'),

  updateSettings: (settings: {
    voice_id?: string;
    speed?: number;
    pitch?: number;
  }) => axiosInstance.put('/voice/settings', settings),

  getAvailableVoices: () => axiosInstance.get('/voice/available-voices'),
};
```

### 10. Privacy Service (`/privacy`)

```typescript
// Analyze text for PII
POST /privacy/analyze
Body: { text: string }

// Get privacy settings
GET /privacy/settings

// Update privacy settings
PUT /privacy/settings
Body: { pii_detection_enabled: boolean, data_retention_days: number }

// Frontend Implementation
export const privacyApi = {
  analyzeText: (text: string) =>
    axiosInstance.post('/privacy/analyze', { text }),

  getSettings: () => axiosInstance.get('/privacy/settings'),

  updateSettings: (settings: {
    pii_detection_enabled?: boolean;
    data_retention_days?: number;
  }) => axiosInstance.put('/privacy/settings', settings),
};
```

### 11. Image Generation (`/image-generation`)

```typescript
// Generate image
POST /image-generation/generate
Body: { prompt: string, style?: string, size?: string }

// Get generation history
GET /image-generation/history?limit=20

// Get image by ID
GET /image-generation/{image_id}

// Frontend Implementation
export const imageGenerationApi = {
  generateImage: (data: {
    prompt: string;
    style?: string;
    size?: string;
  }) => axiosInstance.post('/image-generation/generate', data),

  getHistory: (limit = 20) =>
    axiosInstance.get(`/image-generation/history?limit=${limit}`),

  getImage: (imageId: string) =>
    axiosInstance.get(`/image-generation/${imageId}`),
};
```

### 12. Scheduling (`/scheduling`)

```typescript
// Get user schedule
GET /scheduling/events

// Create event
POST /scheduling/events
Body: { title: string, start_time: string, end_time: string, type: string }

// Update event
PUT /scheduling/events/{event_id}
Body: { title?: string, start_time?: string, end_time?: string }

// Delete event
DELETE /scheduling/events/{event_id}

// Frontend Implementation
export const schedulingApi = {
  getEvents: () => axiosInstance.get('/scheduling/events'),

  createEvent: (event: {
    title: string;
    start_time: string;
    end_time: string;
    type: string;
  }) => axiosInstance.post('/scheduling/events', event),

  updateEvent: (eventId: string, updates: object) =>
    axiosInstance.put(`/scheduling/events/${eventId}`, updates),

  deleteEvent: (eventId: string) =>
    axiosInstance.delete(`/scheduling/events/${eventId}`),
};
```

### 13. Health Check (`/health`)

```typescript
// Basic health check
GET / health;

// Detailed system status
GET / health / detailed;

// Frontend Implementation
export const healthApi = {
  basic: () => axiosInstance.get("/health"),
  detailed: () => axiosInstance.get("/health/detailed"),
};

// React Hook for monitoring
export const useHealthStatus = () => {
  return useQuery({
    queryKey: ["health-status"],
    queryFn: healthApi.basic,
    refetchInterval: 30000, // Check every 30 seconds
  });
};
```

## 🔧 Complete Integration Examples

### 1. Enhanced Chat Page Integration

```typescript
// pages/chat/page.tsx
import { useSendMessage } from "@/services/hooks";
import { ChatComponent } from "@/components/chat-components";

export default function ChatPage() {
  const sendMessageMutation = useSendMessage();

  const handleSendMessage = (message: string) => {
    sendMessageMutation.mutate({
      message,
      include_memory: true,
    });
  };

  // Handle enhanced response from refactored assistant
  const handleChatResponse = (response: any) => {
    // Check for crisis detection
    if (response.crisis_flag) {
      // Show crisis intervention UI
      showCrisisAlert(response.crisis_explanation);
    }

    // Check for schedule suggestions
    if (response.schedule_analysis?.should_suggest_scheduling) {
      // Show schedule opportunity UI
      showScheduleSuggestion(response.schedule_analysis);
    }

    // Check for action plan suggestions
    if (response.action_plan_analysis?.should_suggest_action_plan) {
      // Show action plan UI
      showActionPlanSuggestion(response.action_plan_analysis);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <ChatComponent
        onSendMessage={handleSendMessage}
        onResponse={handleChatResponse}
        loading={sendMessageMutation.isPending}
      />
    </div>
  );
}
```

### 2. Crisis Detection Integration

```typescript
// components/CrisisHandler.tsx
import { useProcessMessage } from "@/services/hooks";
import { AlertDialog } from "@/components/ui/alert-dialog";

export const CrisisHandler = () => {
  const [showCrisisAlert, setShowCrisisAlert] = useState(false);
  const [crisisData, setCrisisData] = useState(null);

  const processMessageMutation = useProcessMessage();

  const handleMessage = async (message: string) => {
    const response = await processMessageMutation.mutateAsync({
      user_id: getCurrentUserId(),
      message,
    });

    if (response.crisis_flag || response.crisis_level === "CRISIS") {
      setCrisisData(response);
      setShowCrisisAlert(true);
    }
  };

  return (
    <>
      {/* Your chat interface */}

      <AlertDialog open={showCrisisAlert} onOpenChange={setShowCrisisAlert}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Crisis Support Available</AlertDialogTitle>
            <AlertDialogDescription>
              {crisisData?.crisis_explanation}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <Button onClick={() => window.open("tel:988")}>
              Call Crisis Hotline (988)
            </Button>
            <Button variant="outline" onClick={() => setShowCrisisAlert(false)}>
              Continue Chatting
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
```

### 3. Action Plan Integration

```typescript
// components/ActionPlanSuggestion.tsx
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const ActionPlanSuggestion = ({
  actionPlanData,
  onAccept,
  onDismiss,
}) => {
  if (!actionPlanData?.should_suggest_action_plan) return null;

  const { action_plan_type, extracted_action_plan } = actionPlanData;

  return (
    <Card className="border-blue-200 bg-blue-50">
      <CardHeader>
        <CardTitle className="text-blue-800">
          {action_plan_type === "therapeutic_emotional"
            ? "🧠 Emotional Wellness Plan"
            : "🎯 Goal Achievement Plan"}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="mb-4">
          I noticed you might benefit from a structured action plan. Would you
          like me to help you create one?
        </p>

        {extracted_action_plan && (
          <div className="mb-4 p-3 bg-white rounded">
            <h4 className="font-semibold">Suggested Steps:</h4>
            <ul className="list-disc list-inside mt-2">
              {extracted_action_plan.steps?.map((step, index) => (
                <li key={index} className="text-sm">
                  {step}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex gap-2">
          <Button onClick={() => onAccept(extracted_action_plan)}>
            Create Action Plan
          </Button>
          <Button variant="outline" onClick={onDismiss}>
            Not Now
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
```

## 🚨 Error Handling Patterns

### Global Error Interceptor

```typescript
// src/services/apis/index.ts
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = "/login";
    } else if (error.response?.status === 403) {
      // Show permission denied message
      toast.error("Permission denied");
    } else if (error.response?.status >= 500) {
      // Show server error message
      toast.error("Server error. Please try again later.");
    }

    return Promise.reject(error);
  }
);
```

### Component Error Handling

```typescript
// Custom hook for error handling
export const useApiCall = <T>(
  apiFunction: () => Promise<T>,
  options?: { showErrorToast?: boolean }
) => {
  return useQuery({
    queryFn: apiFunction,
    onError: (error: any) => {
      if (options?.showErrorToast) {
        toast.error(error.response?.data?.message || "An error occurred");
      }
    },
  });
};
```

## 🔄 Real-time Updates

### WebSocket Integration (if needed)

```typescript
// src/services/websocket.ts
export class WebSocketService {
  private ws: WebSocket | null = null;

  connect(userId: string) {
    this.ws = new WebSocket(`ws://localhost:8000/ws/${userId}`);

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Handle real-time updates
      queryClient.setQueryData(["notifications"], (old: any) => [...old, data]);
    };
  }

  disconnect() {
    this.ws?.close();
  }
}
```

## 📱 Mobile-Specific Considerations

### API Call Optimization for Mobile

```typescript
// Reduce data usage on mobile
export const useOptimizedQuery = <T>(
  key: string[],
  fn: () => Promise<T>,
  isMobile: boolean
) => {
  return useQuery({
    queryKey: key,
    queryFn: fn,
    staleTime: isMobile ? 1000 * 60 * 10 : 1000 * 60 * 5, // Longer stale time on mobile
    cacheTime: isMobile ? 1000 * 60 * 30 : 1000 * 60 * 10, // Longer cache on mobile
  });
};
```

## 🎯 Key Updates for Refactored Assistant

### Enhanced Response Handling

The refactored mental health assistant now provides:

- **Parallel Processing**: Faster response times through concurrent extractions
- **Modular Analysis**: Separate schedule and action plan analysis
- **Crisis Integration**: Maintained crisis detection with improved accuracy
- **Structured Responses**: Clear separation of different analysis types

### New Frontend Patterns

1. **Crisis Handling**: Enhanced crisis detection UI patterns
2. **Action Plans**: Structured action plan suggestion components
3. **Schedule Opportunities**: Wellness check-in suggestion UI
4. **Error Boundaries**: Improved error handling for assistant failures

This quick reference provides all the essential information needed to connect the frontend to the enhanced backend services effectively, including the newly refactored mental health assistant capabilities.
