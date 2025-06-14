import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createQuest, getUserQuests, completeQuest } from "@/services/apis/gamification/quests";
import { CreateQuestType } from "@/app/api/gamification/quests/utils";

export const useQuests = () => {
  return useQuery({
    queryKey: ["quests"],
    queryFn: getUserQuests,
  });
};

export const useCreateQuest = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (quest: CreateQuestType) => createQuest(quest),
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