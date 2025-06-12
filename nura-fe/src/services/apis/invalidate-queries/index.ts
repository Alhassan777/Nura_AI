import { useQueryClient } from "@tanstack/react-query";

export const useInvalidateQueries = () => {
  const queryClient = useQueryClient();
  return {
    invalidateReflectionsQuery: () => {
      queryClient.invalidateQueries({ queryKey: ["reflections"] });
    },
    invalidateBadgesQuery: () => {
      queryClient.invalidateQueries({ queryKey: ["badges"] });
    },
    invalidateQuestsQuery: () => {
      queryClient.invalidateQueries({ queryKey: ["quests"] });
    },
    invalidateUserQuery: () => {
      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  };
};