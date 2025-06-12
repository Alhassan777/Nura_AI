import { Reflection } from "@/types/reflection";
import { TagType } from "@/types/tag";

export type DefaultReflection = Omit<Reflection, "id" | "created_at">;

export const DEFAULT_REFLECTION = {
  mood: "Good",
  note: "",
  tags: [],
  updated_at: new Date().toISOString(),
} as DefaultReflection;