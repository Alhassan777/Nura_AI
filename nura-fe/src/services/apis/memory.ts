import { axiosInstance } from "./index";

export interface MemorySearchResult {
  id: string;
  content: string;
  type: string;
  storage_type: "short_term" | "long_term";
  timestamp: string;
  memory_category: "short_term" | "long_term" | "emotional_anchor";
  is_meaningful: boolean;
  is_lasting: boolean;
  is_symbolic: boolean;
  relevance_score: number;
  metadata: {
    [key: string]: any;
  };
  // Computed for backwards compatibility
  is_emotional_anchor?: boolean;
}

export interface MemorySearchParams {
  query: string;
  limit?: number;
  storage_type?: "short_term" | "long_term" | "all";
  include_anchors?: boolean;
  memory_category?: "short_term" | "long_term" | "emotional_anchor" | "all";
  date_range?: {
    start: string;
    end: string;
  };
}

export interface MemoryStats {
  total: number;
  short_term: number;
  long_term: number;
  emotional_anchors: number;
  sensitive: number;
  categories: {
    short_term: number;
    long_term: number;
    emotional_anchor: number;
  };
  recent_activity: {
    memories_added_today: number;
    memories_added_this_week: number;
    last_memory_timestamp: string;
  };
}

export interface MemoryCategory {
  name: string;
  count: number;
  description: string;
  color: string;
  category_type: "short_term" | "long_term" | "emotional_anchor";
}

// Consolidated Memory API - single source for all memory operations
export const memoryApi = {
  // === BASIC MEMORY OPERATIONS ===

  // Get short-term memories (using memory context)
  getShortTermMemories: async () => {
    const response = await axiosInstance.post("/memory/context", {
      query: null,
    });
    return response.data.context.short_term || [];
  },

  // Get long-term memories
  getLongTermMemories: async () => {
    const response = await axiosInstance.get("/memory/regular-memories");
    return response.data.regular_memories || [];
  },

  // Get emotional anchors
  getEmotionalAnchors: async () => {
    const response = await axiosInstance.get("/memory/emotional-anchors");
    return response.data.emotional_anchors || [];
  },

  // Get all long-term memories (emotional anchors + regular memories)
  getAllLongTermMemories: async () => {
    const response = await axiosInstance.get("/memory/all-long-term");
    return response.data;
  },

  // Get memory stats
  getMemoryStats: async () => {
    const response = await axiosInstance.get("/memory/stats");
    return response.data.stats;
  },

  // Get memory context
  getMemoryContext: async (query?: string) => {
    const response = await axiosInstance.post("/memory/context", {
      query: query || null,
    });
    return response.data.context;
  },

  // === ADVANCED OPERATIONS ===

  // Search memories with advanced filters
  searchMemories: (params: MemorySearchParams) =>
    axiosInstance
      .post("/memory/search", params)
      .then((res) => res.data) as Promise<MemorySearchResult[]>,

  // Get detailed memory statistics
  getDetailedStats: (userId: string) =>
    axiosInstance
      .get(`/memory/detailed-stats/${userId}`)
      .then((res) => res.data) as Promise<MemoryStats>,

  // Delete specific memory
  deleteMemory: (memoryId: string) =>
    axiosInstance.delete(`/memory/${memoryId}`).then((res) => res.data),

  // Delete multiple memories
  deleteMultipleMemories: (memoryIds: string[]) =>
    axiosInstance
      .post("/memory/delete-batch", { memory_ids: memoryIds })
      .then((res) => res.data),

  // Delete memories by category
  deleteByCategory: (category: string, userId: string) =>
    axiosInstance
      .delete(`/memory/delete-category/${category}?user_id=${userId}`)
      .then((res) => res.data),

  // Get memory categories
  getMemoryCategories: (userId: string) =>
    axiosInstance
      .get(`/memory/categories/${userId}`)
      .then((res) => res.data) as Promise<MemoryCategory[]>,

  // Update memory metadata
  updateMemoryMetadata: (memoryId: string, metadata: any) =>
    axiosInstance
      .put(`/memory/metadata/${memoryId}`, metadata)
      .then((res) => res.data),

  // Convert short-term to long-term memory
  promoteToLongTerm: (memoryId: string) =>
    axiosInstance.post(`/memory/promote/${memoryId}`).then((res) => res.data),

  // Convert memory to emotional anchor
  convertToAnchor: (memoryId: string, anchorMetadata?: any) =>
    axiosInstance
      .post(`/memory/convert-to-anchor/${memoryId}`, anchorMetadata || {})
      .then((res) => res.data),

  // Get memory insights and patterns
  getMemoryInsights: (userId: string, timeframe = "month") =>
    axiosInstance
      .get(`/memory/insights/${userId}?timeframe=${timeframe}`)
      .then((res) => res.data),

  // Export memories
  exportMemories: (userId: string, format = "json") =>
    axiosInstance
      .get(`/memory/export/${userId}?format=${format}`, {
        responseType: "blob",
      })
      .then((res) => res.data),

  // Bulk operations
  bulkUpdateMemories: (
    operations: { memory_id: string; action: string; data?: any }[]
  ) =>
    axiosInstance
      .post("/memory/bulk-operations", { operations })
      .then((res) => res.data),

  // Clear all memories (for testing/development)
  clearAllMemories: async () => {
    const response = await axiosInstance.delete("/memory/clear-all");
    return response.data;
  },

  // === PENDING CONSENT OPERATIONS ===

  // Get memories pending consent for long-term storage
  getPendingConsentMemories: async () => {
    const response = await axiosInstance.get("/memory/pending-consent");
    return response.data;
  },

  // Process pending consent memories with user decisions
  processPendingConsent: async (
    memoryChoices: Record<
      string,
      {
        action: "approve" | "deny" | "anonymize";
        pii_handling?: Record<string, { action: string }>;
      }
    >
  ) => {
    const response = await axiosInstance.post(
      "/memory/process-pending-consent",
      {
        memory_choices: memoryChoices,
      }
    );
    return response.data;
  },
};
