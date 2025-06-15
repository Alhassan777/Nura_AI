import { axiosInstance } from "./index";

export interface BrowserCallRequest {
  assistant_id: string;
  metadata?: Record<string, any>;
}

export interface BrowserCallResponse {
  assistantId: string;
  metadata: Record<string, any>;
  publicKey: string;
}

export interface PhoneCallRequest {
  assistant_id: string;
  phone_number: string;
  metadata?: Record<string, any>;
}

export interface PhoneCallResponse {
  call_id: string;
  vapi_call_id?: string;
}

export interface CallStatus {
  call_id: string;
  status: string;
  vapi_call_id?: string;
  created_at: string;
}

export interface VoiceCall {
  id: string;
  user_id: string;
  assistant_id: string;
  channel: string;
  status: string;
  phone_number?: string;
  vapi_call_id?: string;
  created_at: string;
  ended_at?: string;
}

export interface CallSummary {
  id: string;
  call_id: string;
  user_id: string;
  summary_json: any;
  sentiment?: string;
  created_at: string;
}

export const voiceApi = {
  // Initialize a browser-based voice call
  initiateBrowserCall: async (
    request: BrowserCallRequest
  ): Promise<BrowserCallResponse> => {
    const response = await axiosInstance.post("/voice/calls/browser", request);
    return response.data;
  },

  // Create an outbound phone call
  createPhoneCall: async (
    request: PhoneCallRequest
  ): Promise<PhoneCallResponse> => {
    const response = await axiosInstance.post("/voice/calls/phone", request);
    return response.data;
  },

  // Get call status
  getCallStatus: async (callId: string): Promise<CallStatus> => {
    const response = await axiosInstance.get(`/voice/calls/${callId}/status`);
    return response.data;
  },

  // Get user's call history
  getCallHistory: async (limit = 10, offset = 0): Promise<VoiceCall[]> => {
    const response = await axiosInstance.get(
      `/voice/calls?limit=${limit}&offset=${offset}`
    );
    return response.data.calls || [];
  },

  // End a call
  endCall: async (callId: string): Promise<{ success: boolean }> => {
    const response = await axiosInstance.post(`/voice/calls/${callId}/end`);
    return response.data;
  },

  // Get call summary
  getCallSummary: async (callId: string): Promise<CallSummary | null> => {
    try {
      const response = await axiosInstance.get(
        `/voice/calls/${callId}/summary`
      );
      return response.data;
    } catch (error) {
      return null;
    }
  },

  // Get available voices/assistants
  getAvailableVoices: async () => {
    const response = await axiosInstance.get("/voice/voices");
    return response.data.voices || [];
  },

  // Store call metadata (for analytics/debugging)
  storeCallMetadata: async (
    callId: string,
    metadata: Record<string, any>
  ): Promise<{ success: boolean }> => {
    const response = await axiosInstance.post(
      `/voice/calls/${callId}/metadata`,
      {
        metadata,
      }
    );
    return response.data;
  },
};
