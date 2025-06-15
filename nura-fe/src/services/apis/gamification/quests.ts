// Removed legacy import - using backend types
import { axiosInstance } from "../index";

export const getUserQuests = async () => {
  return axiosInstance.get("/gamification/quests").then((res) => res.data);
};

export const createQuest = async (quest: any) => {
  return axiosInstance
    .post("/gamification/quests", quest)
    .then((res) => res.data);
};

export const completeQuest = async (questId: string) => {
  return axiosInstance
    .put(`/gamification/quests/${questId}/complete`)
    .then((res) => res.data);
};
