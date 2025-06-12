import axios from "axios"

export const getUserQuests = async () => {
  return axios.get("/api/gamification/quests").then((res) => res.data);
}