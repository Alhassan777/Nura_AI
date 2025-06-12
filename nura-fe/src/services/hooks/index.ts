import { useMutation, useQuery } from "@tanstack/react-query";
import {
  applyPrivacyChoices,
  getHealthStatus,
  getPrivacyReview,
  sendMessage,
  SendMessageBody,
} from "../apis";
import { memoryApi } from "../apis/memory";

export const useHealthStatus = () => {
  return useQuery({
    queryKey: ["health-status"],
    queryFn: getHealthStatus,
  });
};

export const useSendMessage = () => {
  return useMutation({
    mutationFn: (body: SendMessageBody) => sendMessage(body),
  });
};

export const useGetPrivacyReview = (userId: string) => {
  return useQuery({
    queryKey: ["privacy-review", userId],
    queryFn: () => getPrivacyReview(userId),
  });
};

export const useApplyPrivacyChoices = () => {
  return useMutation({
    mutationFn: (body: { userId: string; choices: any }) =>
      applyPrivacyChoices(body.userId, body.choices),
  });
};

// Memory hooks
export const useMemories = (
  memoryType: "short-term" | "long-term" | "anchors"
) => {
  return useQuery({
    queryKey: ["memories", memoryType],
    queryFn: () => {
      switch (memoryType) {
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
    refetchInterval: 10000, // Refetch every 10 seconds to get new memories
    retry: 2, // Retry failed requests
    retryDelay: 1000, // 1 second delay between retries
  });
};

export const useMemoryStats = () => {
  return useQuery({
    queryKey: ["memory-stats"],
    queryFn: memoryApi.getMemoryStats,
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

export const useDeleteMemory = () => {
  return useMutation({
    mutationFn: (memoryId: string) => memoryApi.deleteMemory(memoryId),
  });
};
