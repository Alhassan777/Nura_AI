import { useQuery } from "@tanstack/react-query";
import { getUserBadges } from "../apis/gamification/index";
import { useAuth } from "@/contexts/AuthContext";

export const useBadges = () => {
  const { user } = useAuth();

  return useQuery({
    queryKey: ["badges"],
    queryFn: getUserBadges,
    enabled: !!user, // Only run when user is authenticated
  });
};
