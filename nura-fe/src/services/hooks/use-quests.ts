import { useQuery } from "@tanstack/react-query";
import { getUserQuests } from "@/services/apis/gamification/quests";

export const useQuests = () => {
  return useQuery({
    queryKey: ["quests"],
    queryFn: getUserQuests,
  });
};