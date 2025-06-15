import { axiosInstance } from "./index";

// TypeScript interfaces for Action Plans
export interface ActionSubtask {
  id: string;
  title: string;
  description?: string;
  completed: boolean;
  due_date?: string;
  created_at: string;
  order_index: number;
}

export interface ActionStep {
  id: string;
  title: string;
  description?: string;
  completed: boolean;
  due_date?: string;
  notes?: string;
  subtasks: ActionSubtask[];
  created_at: string;
  order_index: number;
  time_needed?: string;
  difficulty?: string;
  purpose?: string;
  success_criteria?: string;
}

export interface ActionPlan {
  id: string;
  title: string;
  description?: string;
  plan_type: "therapeutic_emotional" | "personal_achievement" | "hybrid";
  priority: "low" | "medium" | "high";
  status: "active" | "completed" | "paused" | "deleted";
  progress_percentage: number;
  steps: ActionStep[];
  tags: string[];
  due_date?: string;
  created_at: string;
  updated_at: string;
  generated_by_ai: boolean;
  ai_metadata?: any;
}

export interface CreateActionPlanRequest {
  title: string;
  description: string;
  plan_type: "therapeutic_emotional" | "personal_achievement" | "hybrid";
  priority?: "low" | "medium" | "high";
  tags?: string[];
  due_date?: string;
}

export interface UpdateActionPlanRequest {
  title?: string;
  description?: string;
  plan_type?: "therapeutic_emotional" | "personal_achievement" | "hybrid";
  priority?: "low" | "medium" | "high";
  status?: "active" | "completed" | "paused" | "deleted";
  tags?: string[];
  due_date?: string;
}

export interface GenerateActionPlanRequest {
  conversation_context: string;
  user_message: string;
}

// Action Plans API functions
export const actionPlanApi = {
  // Get all action plans
  getActionPlans: async (): Promise<ActionPlan[]> => {
    const response = await axiosInstance.get("/action-plans/");
    return response.data;
  },

  // Get a specific action plan
  getActionPlan: async (planId: string): Promise<ActionPlan> => {
    const response = await axiosInstance.get(`/action-plans/${planId}`);
    return response.data;
  },

  // Create a new action plan
  createActionPlan: async (
    plan: CreateActionPlanRequest
  ): Promise<ActionPlan> => {
    const response = await axiosInstance.post("/action-plans/", plan);
    return response.data;
  },

  // Generate an AI-powered action plan
  generateActionPlan: async (
    request: GenerateActionPlanRequest
  ): Promise<ActionPlan> => {
    const response = await axiosInstance.post(
      "/action-plans/generate",
      request
    );
    return response.data;
  },

  // Update an action plan
  updateActionPlan: async (
    planId: string,
    updates: UpdateActionPlanRequest
  ): Promise<ActionPlan> => {
    const response = await axiosInstance.put(
      `/action-plans/${planId}`,
      updates
    );
    return response.data;
  },

  // Delete an action plan
  deleteActionPlan: async (planId: string): Promise<{ message: string }> => {
    const response = await axiosInstance.delete(`/action-plans/${planId}`);
    return response.data;
  },

  // Update step status
  updateStepStatus: async (
    planId: string,
    stepId: string,
    completed: boolean,
    notes?: string
  ): Promise<ActionPlan> => {
    const response = await axiosInstance.put(
      `/action-plans/${planId}/steps/${stepId}/status`,
      { completed, notes }
    );
    return response.data;
  },

  // Update subtask status
  updateSubtaskStatus: async (
    planId: string,
    stepId: string,
    subtaskId: string,
    completed: boolean
  ): Promise<ActionPlan> => {
    const response = await axiosInstance.put(
      `/action-plans/${planId}/steps/${stepId}/subtasks/${subtaskId}/status`,
      { completed }
    );
    return response.data;
  },

  // Add a new step
  addStep: async (
    planId: string,
    step: { title: string; description?: string }
  ): Promise<ActionPlan> => {
    const response = await axiosInstance.post(
      `/action-plans/${planId}/steps`,
      step
    );
    return response.data;
  },

  // Add a new subtask
  addSubtask: async (
    planId: string,
    stepId: string,
    subtask: { title: string; description?: string }
  ): Promise<ActionPlan> => {
    const response = await axiosInstance.post(
      `/action-plans/${planId}/steps/${stepId}/subtasks`,
      subtask
    );
    return response.data;
  },
};
