import { useMutation, useQuery } from "@tanstack/react-query";
import { addReflection, deleteReflection, getReflections, updateReflection } from "../apis/gamification";
import { DefaultReflection } from "@/constants/default-reflection";
import { useInvalidateQueries } from "../apis/invalidate-queries";


export const useGetReflections = () => {
  return useQuery({
    queryKey: ["reflections"],
    queryFn: getReflections,
  });
};

export const useAddReflection = () => {
  const { invalidateQuestsQuery } = useInvalidateQueries();
  return useMutation({
    mutationFn: addReflection,
    onSuccess: () => {
      invalidateQuestsQuery();
    },
  });
};

export const useDeleteReflection = () => {
  return useMutation({
    mutationFn: (body: { reflectionId: string }) => deleteReflection(body.reflectionId),
  });
};

export const useUpdateReflection = () => {
  return useMutation({
    mutationFn: (body: { reflectionId: string; reflection: Partial<DefaultReflection> }) => updateReflection(body.reflectionId, body.reflection),
  });
};