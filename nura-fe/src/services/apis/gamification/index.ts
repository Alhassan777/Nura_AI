import { axiosInstance } from "../index";

export interface Reflection {
  id: string;
  mood: string;
  note: string;
  tags: string[];
  created_at: string;
  updated_at?: string;
}

export interface Quest {
  id: string;
  key: string;
  title: string;
  description?: string;
  type: string;
  frequency: number;
  time_frame: string;
  xp_reward: number;
  progress: {
    count: number;
    completed: boolean;
    status: string;
    completedAt?: string;
  };
  created_at: string;
}

export interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  threshold_type: string;
  threshold_value: number;
  xp_award: number;
  unlocked: boolean;
}

export interface StreakStats {
  currentStreak: number;
  weekProgress: number;
  monthProgress: number;
}

export interface UserStats {
  user_id: string;
  current_streak: number;
  xp: number;
  freeze_credits: number;
  total_reflections: number;
  completed_quests: number;
  earned_badges: number;
}

// Reflections API
export const getReflections = async (): Promise<Reflection[]> => {
  const response = await axiosInstance.get("/gamification/reflections");
  return response.data;
};

export const createReflection = async (data: {
  mood: string;
  note: string;
  tags: string[];
}): Promise<Reflection> => {
  const response = await axiosInstance.post("/gamification/reflections", data);
  return response.data;
};

export const updateReflection = async (
  reflectionId: string,
  data: {
    mood: string;
    note: string;
    tags: string[];
  }
): Promise<Reflection> => {
  const response = await axiosInstance.put(
    `/gamification/reflections/${reflectionId}`,
    data
  );
  return response.data;
};

export const deleteReflection = async (reflectionId: string): Promise<void> => {
  await axiosInstance.delete(`/gamification/reflections/${reflectionId}`);
};

// Quests API
export const getUserQuests = async (): Promise<{
  systemQuests: Quest[];
  userQuests: Quest[];
}> => {
  const response = await axiosInstance.get("/gamification/quests");
  return response.data;
};

export const createQuest = async (data: {
  title: string;
  description?: string;
  time_frame: string;
  frequency: number;
  xp_reward: number;
}): Promise<Quest> => {
  const response = await axiosInstance.post("/gamification/quests", data);
  return response.data;
};

export const completeQuest = async (
  questId: string
): Promise<{
  quest_id: string;
  status: string;
  count: number;
  required: number;
  xp_awarded: number;
}> => {
  const response = await axiosInstance.put(
    `/gamification/quests/${questId}/complete`
  );
  return response.data;
};

// Badges API
export const getUserBadges = async (): Promise<Record<string, Badge[]>> => {
  const response = await axiosInstance.get("/gamification/badges");
  return response.data;
};

// Streak Stats API
export const getStreakStats = async (): Promise<StreakStats> => {
  const response = await axiosInstance.get("/gamification/streak-stats");
  return response.data;
};

// User Stats API
export const getUserStats = async (): Promise<UserStats> => {
  const response = await axiosInstance.get("/gamification/stats");
  return response.data;
};
