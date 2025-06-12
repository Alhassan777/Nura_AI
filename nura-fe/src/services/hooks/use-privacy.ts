import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { privacyApi } from "../apis/privacy";

export const usePrivacySettings = () => {
  return useQuery({
    queryKey: ["privacy", "settings"],
    queryFn: privacyApi.getSettings,
  });
};

export const useUpdatePrivacySettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: privacyApi.updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["privacy", "settings"] });
    },
  });
};

export const useAnalyzeText = () => {
  return useMutation({
    mutationFn: privacyApi.analyzeText,
  });
};

export const usePrivacyAuditLog = (limit = 50) => {
  return useQuery({
    queryKey: ["privacy", "audit", limit],
    queryFn: () => privacyApi.getAuditLog(limit),
  });
};
