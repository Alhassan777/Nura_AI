import { axiosInstance } from "./index";

export interface AssistantResponse {
  response: string;
  crisis_level: "CRISIS" | "CONCERN" | "SUPPORT";
  crisis_explanation: string;
  schedule_analysis: {
    should_suggest_scheduling: boolean;
    extracted_schedule?: {
      event_type: string;
      suggested_time?: string;
      duration?: number;
      title?: string;
    };
    schedule_opportunity_type?: string;
  };
  action_plan_analysis: {
    should_suggest_action_plan: boolean;
    action_plan_type?: "therapeutic_emotional" | "personal_achievement";
    extracted_action_plan?: {
      action_plan?: {
        plan_title?: string;
        plan_summary?: string;
        immediate_actions?: Array<{
          action: string;
          time_needed?: string;
          difficulty?: "easy" | "moderate" | "challenging";
          purpose?: string;
          success_looks_like?: string;
        }>;
        milestone_goals?: Array<{
          timeframe?: string;
          goal: string;
          action_steps?: string[];
          progress_indicators?: string[];
          potential_obstacles?: string[];
          obstacle_solutions?: string[];
        }>;
        long_term_vision?: {
          timeframe?: string;
          desired_outcome?: string;
          major_milestones?: string[];
          celebration_moments?: string[];
          growth_indicators?: string[];
        };
      };
      // Legacy fallback support
      title?: string;
      description?: string;
      steps?: string[];
      timeline?: string;
      difficulty?: "easy" | "medium" | "hard";
    };
  };
  session_metadata: {
    conversation_turn: number;
    emotional_state_detected: string[];
    topics_discussed: string[];
    memory_references: string[];
  };
  resources_provided: string[];
  coping_strategies: string[];
  timestamp: string;
  crisis_flag: boolean;
  configuration_warning: boolean;
}

export interface CrisisResource {
  id: string;
  name: string;
  type: "hotline" | "text" | "chat" | "website";
  contact_info: string;
  description: string;
  availability: string;
  location?: string;
  urgency_level: "immediate" | "urgent" | "support";
}

export interface ProcessMessagePayload {
  user_id: string;
  message: string;
  conversation_context?: {
    previous_messages?: string[];
    session_id?: string;
    mood_context?: string;
  };
}

// Enhanced Mental Health Assistant API functions
export const assistantApi = {
  // Process message with full assistant capabilities
  processMessage: (data: ProcessMessagePayload) =>
    axiosInstance
      .post("/assistant/process", data)
      .then((res) => res.data) as Promise<AssistantResponse>,

  // Get crisis resources
  getCrisisResources: (location?: string) =>
    axiosInstance
      .get(
        `/assistant/crisis-resources${location ? `?location=${location}` : ""}`
      )
      .then((res) => res.data) as Promise<CrisisResource[]>,

  // Get action plan templates
  getActionPlanTemplates: (type?: string) =>
    axiosInstance
      .get(`/assistant/action-plan-templates${type ? `?type=${type}` : ""}`)
      .then((res) => res.data),

  // Save action plan
  saveActionPlan: (actionPlan: any) =>
    axiosInstance
      .post("/assistant/action-plans", actionPlan)
      .then((res) => res.data),

  // Get user's action plans
  getActionPlans: () =>
    axiosInstance.get("/assistant/action-plans").then((res) => res.data),

  // Update action plan progress
  updateActionPlanProgress: (planId: string, progress: any) =>
    axiosInstance
      .put(`/assistant/action-plans/${planId}/progress`, progress)
      .then((res) => res.data),

  // Get conversation insights
  getConversationInsights: (timeframe = "week") =>
    axiosInstance
      .get(`/assistant/insights?timeframe=${timeframe}`)
      .then((res) => res.data),

  // Report crisis intervention
  reportCrisisIntervention: (data: {
    crisis_level: string;
    actions_taken: string[];
    timestamp: string;
  }) =>
    axiosInstance
      .post("/assistant/crisis-report", data)
      .then((res) => res.data),
};
