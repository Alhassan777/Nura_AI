import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getUserQuests,
  createQuest,
  completeQuest,
  Quest,
} from "../../apis/gamification";

export const useUserQuests = () => {
  return useQuery({
    queryKey: ["user", "quests"],
    queryFn: getUserQuests,
    staleTime: 30000, // 30 seconds
  });
};

export const useCreateQuest = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createQuest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", "quests"] });
    },
  });
};

export const useCompleteQuest = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: completeQuest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", "quests"] });
      queryClient.invalidateQueries({ queryKey: ["user", "stats"] });
      queryClient.invalidateQueries({ queryKey: ["user", "streakStats"] });
    },
  });
};
