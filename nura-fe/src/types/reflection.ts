import { TagType } from "./tag";

export interface Reflection {
  mood: string;
  note: string;
  tags: TagType[];
  created_at: string;
  updated_at: string;
  id: string;
} 