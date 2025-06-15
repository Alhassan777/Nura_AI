import { useQuery } from "@tanstack/react-query";
import { getBadges } from "../apis/gamification/badge";

export const useBadges = () => {
  return useQuery({
    queryKey: ["badges"],
    queryFn: getBadges,
  });
};
