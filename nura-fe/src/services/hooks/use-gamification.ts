import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getReflections,
  createReflection,
  updateReflection,
  deleteReflection,
  getUserStats,
  Reflection,
} from "../apis/gamification";
import { DefaultReflection } from "@/constants/default-reflection";
import { useInvalidateQueries } from "../apis/invalidate-queries";
import { useAuth } from "@/contexts/AuthContext";

// Reflections hooks
export const useReflections = () => {
  return useQuery({
    queryKey: ["user", "reflections"],
    queryFn: getReflections,
    staleTime: 30000, // 30 seconds
  });
};

export const useCreateReflection = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createReflection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", "reflections"] });
      queryClient.invalidateQueries({ queryKey: ["user", "stats"] });
      queryClient.invalidateQueries({ queryKey: ["user", "streakStats"] });
      queryClient.invalidateQueries({ queryKey: ["user", "quests"] });
    },
  });
};

export const useUpdateReflection = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      reflectionId,
      data,
    }: {
      reflectionId: string;
      data: { mood: string; note: string; tags: string[] };
    }) => updateReflection(reflectionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", "reflections"] });
    },
  });
};

export const useDeleteReflection = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteReflection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", "reflections"] });
      queryClient.invalidateQueries({ queryKey: ["user", "stats"] });
    },
  });
};

// User stats hook
export const useUserStats = () => {
  return useQuery({
    queryKey: ["user", "stats"],
    queryFn: getUserStats,
    staleTime: 30000, // 30 seconds
  });
};
