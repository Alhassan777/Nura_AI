import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { memoryApi, MemorySearchParams } from "../apis/memory";

// Search memories
export const useSearchMemories = (params: MemorySearchParams) => {
  return useQuery({
    queryKey: ["memory", "search", params],
    queryFn: () => memoryApi.searchMemories(params),
    enabled: !!params.query,
  });
};

// Get memory statistics
export const useMemoryStats = (userId: string) => {
  return useQuery({
    queryKey: ["memory", "stats", userId],
    queryFn: () => memoryApi.getDetailedStats(userId),
    enabled: !!userId,
  });
};

// Get memory categories
export const useMemoryCategories = (userId: string) => {
  return useQuery({
    queryKey: ["memory", "categories", userId],
    queryFn: () => memoryApi.getMemoryCategories(userId),
    enabled: !!userId,
  });
};

// Get memory insights
export const useMemoryInsights = (userId: string, timeframe = "month") => {
  return useQuery({
    queryKey: ["memory", "insights", userId, timeframe],
    queryFn: () => memoryApi.getMemoryInsights(userId, timeframe),
    enabled: !!userId,
  });
};

// Delete memory
export const useDeleteMemory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (memoryId: string) => memoryApi.deleteMemory(memoryId),
    onSuccess: () => {
      // Invalidate all memory-related queries
      queryClient.invalidateQueries({ queryKey: ["memory"] });
    },
  });
};

// Delete multiple memories
export const useDeleteMultipleMemories = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (memoryIds: string[]) =>
      memoryApi.deleteMultipleMemories(memoryIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memory"] });
    },
  });
};

// Delete memories by category
export const useDeleteByCategory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ category, userId }: { category: string; userId: string }) =>
      memoryApi.deleteByCategory(category, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memory"] });
    },
  });
};

// Get basic memory data
export const useMemories = (type: "short-term" | "long-term" | "anchors") => {
  return useQuery({
    queryKey: ["memory", type],
    queryFn: () => {
      switch (type) {
        case "short-term":
          return memoryApi.getShortTermMemories();
        case "long-term":
          return memoryApi.getLongTermMemories();
        case "anchors":
          return memoryApi.getEmotionalAnchors();
        default:
          return [];
      }
    },
  });
};

// Update memory metadata
export const useUpdateMemoryMetadata = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ memoryId, metadata }: { memoryId: string; metadata: any }) =>
      memoryApi.updateMemoryMetadata(memoryId, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memory"] });
    },
  });
};

// Promote to long-term memory
export const usePromoteToLongTerm = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (memoryId: string) => memoryApi.promoteToLongTerm(memoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memory"] });
    },
  });
};

// Convert to emotional anchor
export const useConvertToAnchor = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      memoryId,
      metadata,
    }: {
      memoryId: string;
      metadata?: any;
    }) => memoryApi.convertToAnchor(memoryId, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memory"] });
    },
  });
};

// Export memories
export const useExportMemories = () => {
  return useMutation({
    mutationFn: ({ userId, format }: { userId: string; format?: string }) =>
      memoryApi.exportMemories(userId, format),
  });
};

// Bulk operations
export const useBulkUpdateMemories = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (
      operations: { memory_id: string; action: string; data?: any }[]
    ) => memoryApi.bulkUpdateMemories(operations),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memory"] });
    },
  });
};

// === PENDING CONSENT HOOKS ===

// Get pending consent memories
export const usePendingConsentMemories = () => {
  return useQuery({
    queryKey: ["memory", "pending-consent"],
    queryFn: () => memoryApi.getPendingConsentMemories(),
    refetchInterval: 30000, // Check for new pending memories every 30 seconds
  });
};

// Process pending consent decisions
export const useProcessPendingConsent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (
      memoryChoices: Record<
        string,
        {
          action: "approve" | "deny" | "anonymize";
          pii_handling?: Record<string, { action: string }>;
        }
      >
    ) => memoryApi.processPendingConsent(memoryChoices),
    onSuccess: () => {
      // Invalidate pending consent and all memory queries
      queryClient.invalidateQueries({
        queryKey: ["memory", "pending-consent"],
      });
      queryClient.invalidateQueries({ queryKey: ["memory"] });
    },
  });
};
