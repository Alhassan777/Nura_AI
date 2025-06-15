import axios from "axios";

export type SendMessageBody = Partial<{
  message?: string;
  include_memory?: boolean;
  endpoint?: string;
  method?: string;
  body?: any;
  conversation_id?: string;
  chat_mode?: "general" | "action_plan" | "visualization";
}>;

export const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

// Add request interceptor to include auth token
axiosInstance.interceptors.request.use(
  (config) => {
    // Only add auth header for non-auth endpoints
    if (typeof window !== "undefined" && !config.url?.includes("/auth/")) {
      const token = localStorage.getItem("auth_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth data and redirect to login
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export const getHealthStatus = async () => {
  return axiosInstance.get("/health").then((res) => res.data);
};

export const sendMessage = async (body: SendMessageBody) => {
  // Use the new multi-modal chat API if chat_mode is specified
  if (body.chat_mode) {
    const multiModalRequest = {
      message: body.message,
      mode: body.chat_mode,
      conversation_id: body.conversation_id,
    };

    const response = await axiosInstance.post(
      "/chat-v2/messages/fast",
      multiModalRequest
    );
    return response.data;
  }

  // Fallback to original assistant API for backward compatibility
  const assistantRequest = {
    message: body.message,
    memory_context: body.include_memory ? {} : null,
    conversation_id: body.conversation_id,
  };

  const response = await axiosInstance.post(
    "/assistant/chat",
    assistantRequest
  );
  return response.data;
};

// Enhanced Chat API functions
export const chatApi = {
  sendMessage: (payload: SendMessageBody) =>
    axiosInstance.post("/chat", payload).then((res) => res.data),

  getChatHistory: (limit = 50, offset = 0) =>
    axiosInstance
      .get(`/chat/history?limit=${limit}&offset=${offset}`)
      .then((res) => res.data),

  clearHistory: () =>
    axiosInstance.delete("/chat/history").then((res) => res.data),

  deleteChatMessage: (messageId: string) =>
    axiosInstance.delete(`/chat/message/${messageId}`).then((res) => res.data),

  getChatSessions: () =>
    axiosInstance.get("/chat/sessions").then((res) => res.data),

  createChatSession: (sessionName?: string) =>
    axiosInstance
      .post("/chat/sessions", { name: sessionName })
      .then((res) => res.data),

  deleteChatSession: (sessionId: string) =>
    axiosInstance.delete(`/chat/sessions/${sessionId}`).then((res) => res.data),
};

export const getPrivacyReview = async (userId: string) => {
  return axiosInstance
    .get(`/memory/privacy-review/${userId}`)
    .then((res) => res.data);
};

export const applyPrivacyChoices = async (userId: string, choices: any) => {
  return axiosInstance
    .post(`/memory/apply-privacy-choices/${userId}`, choices)
    .then((res) => res.data);
};

export const getUser = async () => {
  const response = await axiosInstance.get("/users/profile");
  return response.data;
};

// User Profile API functions
export const userApi = {
  // Get user profile
  getProfile: async () => {
    const response = await axiosInstance.get("/users/profile");
    return response.data;
  },

  // Update user profile
  updateProfile: async (profileData: {
    full_name?: string | null;
    display_name?: string | null;
    bio?: string | null;
    avatar_url?: string | null;
    privacy_settings?: object | null;
  }) => {
    const response = await axiosInstance.put("/users/profile", profileData);
    return response.data;
  },

  // Get user settings
  getSettings: async () => {
    const response = await axiosInstance.get("/users/settings");
    return response.data;
  },

  // Update user settings
  updateSettings: async (settings: object) => {
    const response = await axiosInstance.put("/users/settings", settings);
    return response.data;
  },
};

// Memory API is now consolidated in ./memory.ts
// Import { memoryApi } from "./memory" to use memory functions

export { voiceApi } from "./voice";

export default axiosInstance;
