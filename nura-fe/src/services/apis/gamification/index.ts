import { DefaultReflection } from "@/constants/default-reflection";
import { TagType } from "@/types/tag";
import axios from "axios";

export const getReflections = async () => {
  return axios.get("/api/gamification").then((res) => res?.data);
};

export const addReflection = async (reflection: DefaultReflection) => {
  return axios.post("/api/gamification", reflection).then((res) => res.data);
};

export const deleteReflection = async (reflectionId: string) => {
  return axios.delete(`/api/gamification?reflectionId=${reflectionId}`).then((res) => res.data);
};

export const updateReflection = async (reflectionId: string, reflection: Partial<DefaultReflection>) => {
  return axios.put(`/api/gamification?reflectionId=${reflectionId}`, reflection).then((res) => res.data);
};