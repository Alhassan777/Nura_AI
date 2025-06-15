import { useQuery } from "@tanstack/react-query";
import { getUserBadges } from "./index";

export const useUserBadges = () => {
  return useQuery({
    queryKey: ["user", "badges"],
    queryFn: getUserBadges,
    staleTime: 60000, // 1 minute
  });
};
