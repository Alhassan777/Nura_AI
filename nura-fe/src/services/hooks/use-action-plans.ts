import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

// Mock API functions - these would be replaced with actual API calls
const actionPlansApi = {
  getActionPlans: async () => {
    // Mock data
    return Array.from({ length: 5 }, (_, i) => ({
      id: `plan-${i + 1}`,
      title: `Action Plan ${i + 1}`,
      type: i % 2 === 0 ? "therapeutic_emotional" : "personal_achievement",
      description: `Description for action plan ${i + 1}`,
      steps: Array.from(
        { length: Math.floor(Math.random() * 5) + 2 },
        (_, j) => ({
          id: `step-${i}-${j}`,
          title: `Step ${j + 1}`,
          description: `Description for step ${j + 1}`,
          completed: Math.random() > 0.5,
          due_date: new Date(
            Date.now() + j * 24 * 60 * 60 * 1000
          ).toISOString(),
        })
      ),
      created_at: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
      due_date: new Date(
        Date.now() + (i + 1) * 7 * 24 * 60 * 60 * 1000
      ).toISOString(),
      priority: ["low", "medium", "high"][Math.floor(Math.random() * 3)],
      status: ["active", "completed", "paused"][Math.floor(Math.random() * 3)],
      progress: Math.floor(Math.random() * 100),
      tags: [`tag${i}`, `category${i % 3}`],
    }));
  },

  createActionPlan: async (plan: any) => {
    return {
      id: `plan-${Date.now()}`,
      ...plan,
      created_at: new Date().toISOString(),
    };
  },

  updateActionPlan: async (plan: any) => {
    return plan;
  },

  deleteActionPlan: async (planId: string) => {
    return { success: true };
  },

  getActionPlan: async (planId: string) => {
    return {
      id: planId,
      title: `Action Plan ${planId}`,
      type: "personal_achievement",
      description: "Detailed plan description",
      steps: [],
      created_at: new Date().toISOString(),
      priority: "medium",
      status: "active",
      progress: 50,
      tags: [],
    };
  },
};

export const useActionPlans = () => {
  return useQuery({
    queryKey: ["action-plans"],
    queryFn: actionPlansApi.getActionPlans,
  });
};

export const useCreateActionPlan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: actionPlansApi.createActionPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["action-plans"] });
    },
  });
};

export const useUpdateActionPlan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: actionPlansApi.updateActionPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["action-plans"] });
    },
  });
};

export const useDeleteActionPlan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: actionPlansApi.deleteActionPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["action-plans"] });
    },
  });
};

export const useActionPlan = (planId: string) => {
  return useQuery({
    queryKey: ["action-plans", planId],
    queryFn: () => actionPlansApi.getActionPlan(planId),
    enabled: !!planId,
  });
};
