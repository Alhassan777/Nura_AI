import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  actionPlanApi,
  ActionPlan,
  ActionStep,
  ActionSubtask,
  CreateActionPlanRequest,
  UpdateActionPlanRequest,
} from "../apis/action-plans";

// Export types for use in components
export type { ActionPlan, ActionStep, ActionSubtask };

// Real API functions connecting to backend action plan service
const actionPlansApi = {
  getActionPlans: async (): Promise<ActionPlan[]> => {
    const response = await actionPlanApi.getActionPlans();
    return response;
  },

  createActionPlan: async (
    plan: Omit<
      ActionPlan,
      | "id"
      | "created_at"
      | "updated_at"
      | "progress_percentage"
      | "generated_by_ai"
      | "ai_metadata"
    >
  ): Promise<ActionPlan> => {
    const newPlan: CreateActionPlanRequest = {
      title: plan.title,
      description: plan.description || "",
      plan_type: plan.plan_type,
      priority: plan.priority,
      tags: plan.tags,
      due_date: plan.due_date,
    };

    return await actionPlanApi.createActionPlan(newPlan);
  },

  updateActionPlan: async (
    plan: Partial<ActionPlan> & { id: string }
  ): Promise<ActionPlan> => {
    const { id, ...updates } = plan;
    const updatedPlan: UpdateActionPlanRequest = {
      title: updates.title,
      description: updates.description,
      plan_type: updates.plan_type,
      priority: updates.priority,
      status: updates.status,
      tags: updates.tags,
      due_date: updates.due_date,
    };

    return await actionPlanApi.updateActionPlan(id, updatedPlan);
  },

  deleteActionPlan: async (planId: string): Promise<{ success: boolean }> => {
    await actionPlanApi.deleteActionPlan(planId);
    return { success: true };
  },

  getActionPlan: async (planId: string): Promise<ActionPlan> => {
    const plan = await actionPlanApi.getActionPlan(planId);
    return plan;
  },

  updateStepStatus: async (
    planId: string,
    stepId: string,
    completed: boolean,
    notes?: string
  ): Promise<ActionPlan> => {
    return await actionPlanApi.updateStepStatus(
      planId,
      stepId,
      completed,
      notes
    );
  },

  updateSubtaskStatus: async (
    planId: string,
    stepId: string,
    subtaskId: string,
    completed: boolean
  ): Promise<ActionPlan> => {
    return await actionPlanApi.updateSubtaskStatus(
      planId,
      stepId,
      subtaskId,
      completed
    );
  },

  addStep: async (
    planId: string,
    step: { title: string; description?: string }
  ): Promise<ActionPlan> => {
    return await actionPlanApi.addStep(planId, step);
  },

  addSubtask: async (
    planId: string,
    stepId: string,
    subtask: { title: string; description?: string }
  ): Promise<ActionPlan> => {
    return await actionPlanApi.addSubtask(planId, stepId, subtask);
  },
};

// Helper function to calculate dynamic progress
export const calculateProgress = (steps: ActionStep[]): number => {
  if (!steps || steps.length === 0) return 0;

  let totalItems = 0;
  let completedItems = 0;

  steps.forEach((step) => {
    if (step.subtasks && step.subtasks.length > 0) {
      // If step has subtasks, count subtasks
      totalItems += step.subtasks.length;
      completedItems += step.subtasks.filter(
        (subtask) => subtask.completed
      ).length;
    } else {
      // If no subtasks, count the step itself
      totalItems += 1;
      if (step.completed) {
        completedItems += 1;
      }
    }
  });

  return totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;
};

// React Query hooks
export const useActionPlans = () => {
  return useQuery({
    queryKey: ["action-plans"],
    queryFn: actionPlansApi.getActionPlans,
  });
};

export const useActionPlan = (planId: string) => {
  return useQuery({
    queryKey: ["action-plans", planId],
    queryFn: () => actionPlansApi.getActionPlan(planId),
    enabled: !!planId,
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
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["action-plans"] });
      queryClient.setQueryData(["action-plans", data.id], data);
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

export const useUpdateStepStatus = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      planId,
      stepId,
      completed,
      notes,
    }: {
      planId: string;
      stepId: string;
      completed: boolean;
      notes?: string;
    }) => actionPlansApi.updateStepStatus(planId, stepId, completed, notes),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["action-plans"] });
      queryClient.setQueryData(["action-plans", data.id], data);
    },
  });
};

export const useUpdateSubtaskStatus = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      planId,
      stepId,
      subtaskId,
      completed,
    }: {
      planId: string;
      stepId: string;
      subtaskId: string;
      completed: boolean;
    }) =>
      actionPlansApi.updateSubtaskStatus(planId, stepId, subtaskId, completed),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["action-plans"] });
      queryClient.setQueryData(["action-plans", data.id], data);
    },
  });
};

export const useAddStep = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      planId,
      step,
    }: {
      planId: string;
      step: { title: string; description?: string };
    }) => actionPlansApi.addStep(planId, step),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["action-plans"] });
      queryClient.setQueryData(["action-plans", data.id], data);
    },
  });
};

export const useAddSubtask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      planId,
      stepId,
      subtask,
    }: {
      planId: string;
      stepId: string;
      subtask: { title: string; description?: string };
    }) => actionPlansApi.addSubtask(planId, stepId, subtask),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["action-plans"] });
      queryClient.setQueryData(["action-plans", data.id], data);
    },
  });
};
