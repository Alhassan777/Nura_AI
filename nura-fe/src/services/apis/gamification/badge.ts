import axios from "axios";

export const getBadges = async () => {
  return axios.get(`/api/gamification/badges`).then((res) => res.data);
};

