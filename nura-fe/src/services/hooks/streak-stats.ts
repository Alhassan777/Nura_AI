import { useQuery } from "@tanstack/react-query";
import axios from "axios";

interface StreakStats {
  currentStreak: number;
  weekProgress: number;
  monthProgress: number;
}

export const useStreakStats = () => {
  return useQuery<StreakStats>({
    queryKey: ["streak-stats"],
    queryFn: async () => {
      const { data } = await axios.get("/api/gamification/streak-stats");
      return data;
    },
  });
};
