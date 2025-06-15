import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createQuest,
  getUserQuests,
  completeQuest,
} from "@/services/apis/gamification/quests";
// Removed legacy import - using backend types
import { useAuth } from "@/contexts/AuthContext";

export const useQuests = () => {
  const { user } = useAuth();

  return useQuery({
    queryKey: ["quests"],
    queryFn: getUserQuests,
    enabled: !!user, // Only run when user is authenticated
  });
};

export const useCreateQuest = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (quest: any) => createQuest(quest),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["quests"] });
    },
  });
};

export const useCompleteQuest = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (questId: string) => completeQuest(questId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["quests"] });
    },
  });
};
