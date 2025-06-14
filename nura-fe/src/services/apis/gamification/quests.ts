import { CreateQuestType } from "@/app/api/gamification/quests/utils";
import axios from "axios"

export const getUserQuests = async () => {
  return axios.get("/api/gamification/quests").then((res) => res.data);
}

export const createQuest = async (quest: CreateQuestType) => {
  return axios.post("/api/gamification/quests", quest).then((res) => res.data);
};

export const completeQuest = async (questId: string) => {
  return axios.put("/api/gamification/quests", { questId }).then((res) => res.data);
};