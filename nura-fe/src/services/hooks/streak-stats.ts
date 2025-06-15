import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { axiosInstance } from "@/services/apis";

export type StreakStats = {
  currentStreak: number;
  weekProgress: number;
  monthProgress: number;
};

export const useStreakStats = () => {
  const { user } = useAuth();

  return useQuery<StreakStats>({
    queryKey: ["streak-stats"],
    queryFn: async () => {
      const { data } = await axiosInstance.get("/gamification/streak-stats");
      return data;
    },
    enabled: !!user, // Only run when user is authenticated
  });
};
