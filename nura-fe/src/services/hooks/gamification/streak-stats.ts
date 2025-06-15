import { useQuery } from "@tanstack/react-query";
import { getStreakStats } from "../../apis/gamification";

export const useStreakStats = () => {
  return useQuery({
    queryKey: ["user", "streakStats"],
    queryFn: getStreakStats,
    staleTime: 30000, // 30 seconds
  });
};
