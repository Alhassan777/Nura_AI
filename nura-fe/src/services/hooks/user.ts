import { useState, useEffect } from "react";
import axios from "axios";
import { Reflection } from "@/types/reflection";
import { getUser } from "../apis";
import { useQuery } from "@tanstack/react-query";

export interface UserProfile {
  // Add fields specific to your user_profiles table
  // This is just an example - customize based on your schema
  user_id: string;
  display_name?: string;
  bio?: string;
  avatar_url?: string;
  xp?: number;
  level?: number;
  created_at?: string;
  updated_at?: string;
  preferences?: Record<string, any>;
  [key: string]: any; // Allow for additional fields
}

export interface UserData {
  id: string;
  email: string | null;
  emailVerified: boolean;
  createdAt: string;
  updatedAt: string | null;
  lastSignInAt: string | null;
  metadata: Record<string, any>;
  profile: UserProfile | null;
  current_streak: number;
  xp: number;
  freeze_credits: number;
  reflections: Reflection[] | null;
}

interface UseUserResult {
  user: UserData | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export const useUser = () => {
  return useQuery({
    queryKey: ["user"],
    queryFn: () => getUser(),
  });
};
